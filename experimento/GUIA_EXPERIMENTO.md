# Experimento HU2.1.1 · Colocalización de Suscripción, Pólizas y Pagos en la decisión y emisión automática

Guía en tres partes: (1) texto de Planeación listo para Hélix, (2) procedimiento de ejecución con la consola de AWS, (3) plantilla del documento de Ejecución (resultados y análisis) y guion del video. Todo sigue la estructura de `Lab3_Diseño_del_experimentov3.pdf` y `Lab3_Ejecucion_del_experimentov2.pdf`.

---

## PARTE 0 · Código base (ya aplicado)

El refactor a 12 módulos ya está hecho y en `origin/feature/refactor-12-modulos` (entidades, transacción atómica de emisión, idempotencia, versión optimista, `data-source.ts`, `batch.ts`, Docker, etc. — ver `CLAUDE.md` en la raíz). Esta rama de experimento (`feature/experimento-hu211`) parte de ahí, así que **no hay que descomprimir ningún zip ni borrar entidades a mano**: solo falta lo que completa este kit (Parte A del endpoint y Parte B de este documento).

Si en algún momento necesita partir de cero desde `main`:

```powershell
cd C:\Users\ximen\OneDrive\Documentos\solventa-backend
git fetch origin
git checkout -b feature/experimento-hu211 origin/feature/refactor-12-modulos
npm install
npm run build   # debe terminar sin errores
```

Antes de hacer merge a `main`, coordine con el compañero dueño de la rama `feature/hu112-rolling-update-reglas-rating`, porque el refactor modifica `src/cotizacion` (este kit de experimento no la toca).

---

## PARTE 1 · Planeación (texto para Hélix >> Experimentos >> + Nuevo >> Planeación)

### Nombre
Colocalización de Suscripción, Pólizas y Pagos para la decisión y emisión automática de la póliza (HU2.1.1).

### Hipótesis de diseño
Si la decisión de suscripción, la emisión de la póliza y el registro del cobro de la prima se ejecutan como invocaciones en-proceso entre los módulos Suscripción y emisión, Pólizas y Pagos del monolito modular, dentro de una única transacción de base de datos, reutilizando el perfil de riesgo ya calculado y dejando fuera del camino crítico las llamadas a la pasarela de pago y a la firma electrónica, entonces la decisión más la emisión de una solicitud que cumple el perfil de riesgo se completará con p95 ≤ 1,5 s y p99 ≤ 3 s en operación normal (50 TPS), con una tasa de error inferior al 1 %, porque el camino crítico se reduce a una lectura indexada y tres inserciones sobre una misma conexión, sin saltos de red entre módulos ni serialización HTTP intermedia.

Nota de alcance. La hipótesis afirma que el diseño colocalizado es suficiente para cumplir el ASR en el rango de carga probado; no compara contra una variante con HTTP entre módulos, así que no demuestra que evitar HTTP sea la causa exclusiva del cumplimiento. El cobro queda registrado en estado pendiente dentro de la transacción y se procesa después contra la pasarela (monitor de independencia emisión/pago del modelo de concurrencia); la firma electrónica tampoco se mide. Ambas exclusiones son decisiones de diseño declaradas, no simplificaciones ocultas.

### Escenario de calidad vinculado
HU2.1.1 · Latencia. Fuente: cliente asegurado. Estímulo: acepta la cotización y solicita que su solicitud sea aprobada automáticamente cuando cumple el perfil de riesgo. Artefacto: servicio de suscripción y emisión. Ambiente: operación normal (50 TPS). Respuesta: decisión aprobada y póliza emitida con su cobro de prima registrado. Medida: p95 < 1500 ms y p99 < 3000 ms, medidos sobre la ruta de aprobación automática.

### Tácticas y patrones
Localización de recursos (colocalización). Suscripción, Pólizas y Pagos viven en el mismo proceso de la API Solventa y se comunican por invocación directa de métodos de servicio, tal como muestra el hilo "Núcleo de venta" del modelo de concurrencia.
¿Por qué esta táctica y no otra? La alternativa sería separar Pólizas o Pagos en servicios (Fase 2), lo que añade al menos dos saltos de red y la necesidad de coordinar una transacción distribuida (saga o 2PC) para no dejar pólizas sin cobro; en la Fase 1 la presión de negocio es salir rápido y barato, y el ASR es de latencia sobre un flujo que debe ser atómico, así que la colocalización es la opción de menor costo y menor latencia.

Transacción atómica compartida (conector en-proceso con EntityManager común). La suscripción, la póliza y el pago pendiente se guardan en una sola transacción; si algo falla, no queda nada a medias.
¿Por qué esta táctica y no otra? Tres `save()` independientes serían marginalmente más rápidos pero violarían HU2.3.1 (cero pérdida o duplicación); una saga con compensaciones es propia de servicios distribuidos y aquí añadiría complejidad sin beneficio.

Idempotencia por restricción de unicidad. `cotizacionId` es único en `suscripciones` y la clave `prima:{polizaId}` es única en `pagos`; un reintento devuelve la decisión ya tomada.
¿Por qué esta táctica y no otra? Un mutex en memoria no funciona con varias réplicas (la API no guarda estado para poder escalar horizontalmente); la unicidad en la base de datos es la única garantía que sobrevive a réplicas y reintentos, y cuesta un índice.

Semáforo de conexiones a la base de datos (pool acotado, `DB_POOL_MAX`). Limita cuántas transacciones concurrentes llegan a PostgreSQL, protegiendo a la base de datos bajo picos.
¿Por qué esta táctica y no otra? Un pool ilimitado traslada la contención a PostgreSQL (bloqueos, cambios de contexto) y degrada la cola de latencia de forma impredecible; un pool acotado convierte la sobrecarga en espera medible dentro de la API, que es justamente lo que el experimento busca observar.

Reducción de overhead computacional. La decisión es una comparación de umbrales sobre el score del `PerfilRiesgo` ya calculado (O(1)); no se recalcula el perfil ni se consulta Open Finance dentro de la transacción. Se reporta como factor que contribuye, no como hipótesis independiente.

### Diseño del experimento
Variable independiente: tasa de llegada de solicitudes (TPS), en una escalera de siete niveles con tasa constante (modelo de llegada abierto de k6, `constant-arrival-rate`): smoke 2 TPS durante 60 s (1 repetición), carga baja 10 TPS (4), carga media 25 TPS (4), operación normal 50 TPS (8), carga alta 100 TPS (4), carga muy alta 200 TPS (4) y estrés 400 TPS (8); cada corrida no smoke dura 180 s. Operación normal y estrés tienen más repeticiones por ser el nivel de referencia del ASR y el nivel donde se espera la mayor varianza.

Variables dependientes: p95, p99, promedio, mínimo, máximo y desviación estándar de la latencia de las solicitudes aprobadas; throughput logrado (solicitudes completadas por segundo); tasa de error (%). Como información complementaria se reportan por separado las latencias de las rutas de revisión asistida y rechazo, y el uso de CPU de las instancias.

Variables controladas: las mismas tres instancias EC2 (tipos, región us-east-1, misma zona de disponibilidad, créditos t3 en modo unlimited), la misma imagen de la aplicación, `DB_POOL_MAX=10`, PostgreSQL 16 con `max_connections=200`, base de datos reiniciada al estado semilla antes de cada corrida, el mismo dataset (20 productos; una cotización nueva por solicitud, ya que `cotizacionId` es único; scores distribuidos 70 % aprobación, 20 % revisión, 10 % rechazo), los mismos umbrales de decisión (0,7 y 0,4), 60 s de enfriamiento entre corridas y el batch de perfiles apagado durante el experimento (recalcula scores y alteraría las decisiones).

Condición de validez: una corrida solo cuenta como cumplimiento del ASR si además de p95 y p99 dentro de la meta tiene tasa de error < 1 %; con más errores, las latencias de las peticiones exitosas no representan la experiencia del cliente.

Software a escribir: endpoint `POST /suscripciones` (SuscripcionController y SuscripcionService) con invocación en-proceso a `PolizasService.emitir()` y `PagosService.cobrarPrima()` dentro de la transacción; script SQL de reinicio y semilla; script k6 parametrizado por nivel; script de escalera que reinicia la BD, verifica `/health`, enfría y corre k6; script Python de consolidación y figuras; archivos de despliegue (Dockerfile, docker-compose de la BD y de la API, user data de las EC2).

Procedimiento:
1. Iniciar el Learner Lab y abrir la consola de AWS; verificar el presupuesto en Cost Explorer.
2. Crear en la consola de EC2 los grupos de seguridad de la aplicación, la base de datos y el generador de carga.
3. Lanzar tres instancias EC2 Ubuntu 24.04 en la misma zona: `solventa-db` y `solventa-app` (t3.medium, con Docker) y `solventa-loadgen` (t3.small, con k6).
4. En `solventa-db`, levantar PostgreSQL con Docker; en `solventa-app`, clonar el repositorio y levantar la API apuntando a la IP privada de la base de datos.
5. Desde `solventa-loadgen`, verificar `GET /health` por la IP privada de la aplicación.
6. Ejecutar el smoke test para validar el circuito extremo a extremo (las tres decisiones, cero decisiones inesperadas) y calibrar el script.
7. Ejecutar la escalera completa (33 corridas, aproximadamente 2,5 h), reiniciando la base de datos antes de cada corrida, mientras se observa la pestaña Monitoring de las instancias.
8. Consolidar las corridas por nivel, construir las figuras de p95/p99, error y throughput, y determinar el punto de inflexión (mayor nivel en que se cumple el ASR con error < 1 %).
9. Recolectar la evidencia (capturas de consola, salidas de k6, prompts de IAG), terminar las instancias, borrar los grupos de seguridad y revisar Cost Explorer; finalizar con End Lab.

### Recursos requeridos
Cuenta AWS Academy Learner Lab (Vocareum), región us-east-1. Tres instancias EC2 Ubuntu Server 24.04 LTS en la misma subred: `solventa-app` (t3.medium, API NestJS en Docker), `solventa-db` (t3.medium, PostgreSQL 16 en Docker) y `solventa-loadgen` (t3.small, k6 y cliente psql). Par de llaves `vockey` (archivo `labsuser.pem`). Tres grupos de seguridad: `sg-solventa-loadgen` (SSH 22 desde la IP del equipo), `sg-solventa-app` (SSH 22 desde la IP del equipo; TCP 3000 desde `sg-solventa-loadgen` y desde la IP del equipo) y `sg-solventa-db` (SSH 22 desde la IP del equipo; TCP 5432 desde `sg-solventa-app` y `sg-solventa-loadgen`). El generador de carga se ubica dentro de la misma VPC y zona para no medir el tiempo de red Bogotá–Virginia y para no competir por CPU con la API. Repositorio del equipo con `Dockerfile`, `experimento/` y `.env.experimento.example`; k6; Python 3 con matplotlib en el equipo local para consolidar; hoja de cálculo. Costo estimado: aproximadamente USD 0,10 por hora con las tres instancias encendidas.

### Elementos de arquitectura involucrados
Vista funcional: componentes Suscripción y emisión, Pólizas y Pagos (camino crítico), con lecturas de Cotización y Perfilamiento; conectores "emite" y "cobro de prima" implementados como invocación en-proceso con transacción compartida. Vista de información: clases Suscripcion, Poliza, Pago, Cotizacion y PerfilRiesgo; tablas `suscripciones`, `polizas`, `pagos`, `cotizaciones` y `perfiles_riesgo`. Vista de concurrencia: proceso API Solventa, hilo de petición del núcleo de venta, semáforo de conexiones a la BD y monitor de independencia emisión/pago. Vista de despliegue: nodo de aplicación y capa de datos separados (fragmento de la región primaria, una zona de disponibilidad), más el nodo generador de carga propio del experimento.

### Esfuerzo estimado
12 horas-persona: 2 h ajuste del endpoint y del camino transaccional, 2 h script k6 y semilla de datos, 1,5 h aprovisionamiento en AWS (grupos de seguridad, tres instancias, despliegue y smoke), 3 h ejecución de la escalera con monitoreo (2,5 h de corridas más contingencia), 1,5 h consolidación, figuras y punto de inflexión, 2 h documentación, evidencia y video.

---

## PARTE 2 · Ejecución paso a paso en AWS

Tenga abierto un archivo de notas para anotar IPs y la hora de inicio y fin de cada fase (esfuerzo real). Tome captura de cada paso marcado con 📸.

### 2.1 Iniciar el laboratorio
1. Canvas >> AWS Academy Learner Lab >> Modules >> Iniciar el laboratorio >> **Start Lab**. Espere el círculo verde junto a "AWS".
2. En **AWS Details** descargue `labsuser.pem` (Download PEM) y guárdelo en `C:\Users\ximen\.ssh\labsuser.pem`. En PowerShell, restrinja permisos (si no, SSH lo rechaza):
   ```powershell
   icacls $HOME\.ssh\labsuser.pem /inheritance:r /grant:r "$($env:USERNAME):(R)"
   ```
3. Clic en **AWS** para abrir la consola. Verifique arriba a la derecha la región **N. Virginia (us-east-1)**.
4. 📸 Billing and Cost Management >> Cost Explorer (costo antes de empezar).

### 2.2 Grupos de seguridad (EC2 >> Network & Security >> Security Groups >> Create security group)
Cree los tres en la VPC por defecto, en este orden (el segundo y el tercero referencian a los anteriores):

1. `sg-solventa-loadgen`: Inbound SSH (22), Source **My IP**.
2. `sg-solventa-app`: Inbound SSH (22) My IP; Custom TCP 3000, Source = `sg-solventa-loadgen`; Custom TCP 3000, Source My IP (para mostrar `/health` en el video).
3. `sg-solventa-db`: Inbound SSH (22) My IP; PostgreSQL (5432), Source = `sg-solventa-app`; PostgreSQL (5432), Source = `sg-solventa-loadgen` (la semilla se carga desde el generador).

📸 La lista de los tres grupos con sus reglas de entrada.

### 2.3 Lanzar las tres instancias (EC2 >> Instances >> Launch instances)
Para cada una: AMI **Ubuntu Server 24.04 LTS**, Key pair **vockey**, en *Network settings* clic en **Edit** y elija la **misma subnet** (por ejemplo, la de us-east-1a) para las tres, *Select existing security group*, almacenamiento 20 GiB gp3. En *Advanced details*: **Credit specification = Unlimited** y pegue el *User data* indicado.

| Nombre | Tipo | Security group | User data |
|---|---|---|---|
| solventa-db | t3.medium | sg-solventa-db | `experimento/infra/user-data-docker.sh` |
| solventa-app | t3.medium | sg-solventa-app | `experimento/infra/user-data-docker.sh` |
| solventa-loadgen | t3.small | sg-solventa-loadgen | `experimento/infra/user-data-loadgen.sh` |

Opcional pero recomendado: en la instancia seleccionada, *Actions >> Monitor and troubleshoot >> Manage detailed monitoring >> Enable* (métricas cada minuto en lugar de cada cinco).

Anote para cada instancia la **IP pública** (para SSH) y la **IP privada** (para el tráfico entre ellas). 📸 Lista de instancias en estado *Running* con *Status check 2/2*.

Espere unos 3 minutos y verifique que el user data terminó (debe existir el archivo): `ls ~/user-data-ok`.

### 2.4 Base de datos (SSH a solventa-db)
```powershell
ssh -i $HOME\.ssh\labsuser.pem ubuntu@<IP_PUBLICA_DB>
```
```bash
git clone https://github.com/ximenazelaya1989/solventa.git
# Si el repositorio es privado: git clone https://<TOKEN_GITHUB>@github.com/ximenazelaya1989/solventa.git
cd solventa && git checkout feature/experimento-hu211
cd experimento/docker
sudo docker compose -f docker-compose.db.yml up -d
sudo docker ps          # 📸 contenedor postgres:16 "Up"
```

### 2.5 Aplicación (SSH a solventa-app)
```bash
git clone https://github.com/ximenazelaya1989/solventa.git
cd solventa && git checkout feature/experimento-hu211
cp experimento/.env.experimento.example experimento/.env.experimento
sed -i 's/^DB_HOST=.*/DB_HOST=<IP_PRIVADA_DB>/' experimento/.env.experimento
cd experimento/docker
sudo docker compose -f docker-compose.app.yml up -d --build   # 3-5 min la primera vez
sudo docker compose -f docker-compose.app.yml logs --tail 30  # debe decir que Nest arrancó
curl http://localhost:3000/health                            # {"status":"ok"}
```
La API crea las tablas al arrancar (`DB_SYNCHRONIZE=true`, solo en este entorno desechable). Déjela corriendo. Para observar recursos durante las corridas: `sudo docker stats`.

### 2.6 Generador de carga (SSH a solventa-loadgen)
```bash
git clone https://github.com/ximenazelaya1989/solventa.git
cd solventa && git checkout feature/experimento-hu211
cd experimento && chmod +x scripts/correr-escalera.sh
export BASE_URL=http://<IP_PRIVADA_APP>:3000
export DB_HOST=<IP_PRIVADA_DB>
curl $BASE_URL/health                                         # 📸
```

### 2.7 Smoke test
```bash
./scripts/correr-escalera.sh smoke
cat resultados/smoke-rep1.json
```
Verifique en el JSON: `tasaError` = 0, `decisionesInesperadas` = 0, y conteos por decisión cercanos a 70/20/10 %. Si hay decisiones inesperadas, el batch de perfiles se ejecutó o la semilla no corrió: no siga hasta corregirlo. 📸 Salida del smoke.

### 2.8 Escalera completa (dentro de tmux, para que no se corte si se cae el SSH)
```bash
tmux new -s escalera
export BASE_URL=http://<IP_PRIVADA_APP>:3000
export DB_HOST=<IP_PRIVADA_DB>
./scripts/correr-escalera.sh 2>&1 | tee resultados/escalera.log
# Salir sin detener: Ctrl+B y luego D.  Volver: tmux attach -t escalera
```
Duración aproximada 2,5 h (la sesión del Learner Lab dura 4 h; empiece con margen). Mientras corre:
1. 📸 EC2 >> solventa-app >> pestaña **Monitoring** (CPU utilization) durante operación normal y durante estrés; lo mismo para solventa-db.
2. 📸 Terminal de solventa-app con `sudo docker stats` en estrés.
3. 📸 Terminal del generador mostrando k6 en ejecución (útil para el video).

Si solo tiene tiempo para una parte, priorice smoke, operación normal y estrés: `./scripts/correr-escalera.sh operacion-normal` y `./scripts/correr-escalera.sh estres`.

### 2.9 Descargar y consolidar (en su equipo)
```powershell
cd C:\Users\ximen\OneDrive\Documentos\solventa-backend\experimento
scp -i $HOME\.ssh\labsuser.pem -r ubuntu@<IP_PUBLICA_LOADGEN>:~/solventa/experimento/resultados .
$py = "C:\Users\ximen\AppData\Local\Programs\Python\Python313\python.exe"
& $py -m pip install matplotlib
& $py analisis\consolidar.py resultados
```
Resultado: `analisis/tabla-resultados.csv` y las figuras `fig-latencia.png`, `fig-error.png`, `fig-throughput.png`; en consola se imprime el punto de inflexión. Suba `resultados/` y `analisis/` al repositorio (son evidencia).

### 2.10 Limpieza (obligatoria)
1. EC2 >> Instances >> seleccione las tres >> *Instance state >> Terminate*. Espere *Terminated*. 📸
2. EC2 >> Volumes: verifique que no quedan volúmenes *available* (si queda alguno, *Delete*).
3. Security Groups: borre `sg-solventa-db`, luego `sg-solventa-app`, luego `sg-solventa-loadgen`.
4. 📸 Cost Explorer con el costo final del experimento (puede tardar horas en reflejarse; tome la captura al día siguiente si hace falta).
5. Vocareum >> **End Lab**.

---

## PARTE 3 · Documento de Ejecución (PDF para el repositorio y enlace en Hélix)

Estructura igual a `Lab3_Ejecucion_del_experimentov2.pdf`. Los valores entre `<>` salen de su ejecución real; no invente cifras.

### Vistas de arquitectura
Figura 1, vista de despliegue del experimento: VPC us-east-1, subred de una zona; nodo `solventa-loadgen` (k6) → HTTP 3000 → nodo `solventa-app` (Docker, NestJS: módulos Suscripción, Pólizas, Pagos, Cotización, Perfilamiento) → TCP 5432 → nodo `solventa-db` (Docker, PostgreSQL 16). Indique que es un fragmento de la región primaria / zona A de la vista de despliegue del proyecto, sin balanceador ni réplicas porque el ASR es de latencia en operación normal, no de escalabilidad.
Figura 2, fragmento de la vista funcional: Suscripción y emisión → emite → Pólizas → cobro de prima → Pagos, con lecturas a Cotización y Perfilamiento; anote sobre los conectores "invocación en-proceso, transacción compartida".
Opcional, fragmento de concurrencia: hilo de petición del núcleo de venta, semáforo de conexiones BD y monitor de independencia emisión/pago.

### Resultados
Duración real: `<X>` horas-persona frente a 12 estimadas; explique la desviación. Artefactos construidos: tres EC2, tres grupos de seguridad, contenedores de API y BD, script k6, semilla, escalera y consolidación, `<N>` corridas.

Tabla (desde `tabla-resultados.csv`), columnas: Nivel, TPS objetivo, Repeticiones, p95 (ms), p99 (ms), Promedio (ms), Desv. estándar (ms), Throughput logrado (req/s), Error %, ¿Cumple ASR?. Resalte la fila del punto de inflexión: el último nivel que cumple, o el primero que deja de cumplir, igual que el ejemplo de Lab3.

Figuras: `fig-latencia.png` (p95/p99 contra nivel con líneas de 1500 y 3000 ms), `fig-error.png` (con la línea de 1 %), `fig-throughput.png` (logrado contra objetivo). Capturas de consola AWS y de k6 como evidencia.

### Análisis (guía de lo que debe discutir)
1. Cumplimiento en operación normal (50 TPS): valores de p95/p99 frente a 1500/3000 ms y margen porcentual.
2. Punto de inflexión: a qué nivel se deja de cumplir y cuál de las tres métricas cae primero (p99, p95 o error).
3. Cuello de botella: compare CPU de solventa-app y solventa-db en ese nivel. Si la API tiene CPU alta y la BD no, el límite es el event loop de Node.js; si ambas están bajas pero la latencia crece, es la espera por el pool de 10 conexiones (el semáforo está funcionando como se diseñó); si la BD está alta, es la escritura en PostgreSQL.
4. Throughput: si el logrado se separa del objetivo, el sistema está saturado (meseta, como en el ejemplo de Lab3).
5. Costo de las tácticas: la transacción atómica y la idempotencia añaden una lectura previa y restricciones de unicidad; discuta si su costo es visible frente a la latencia total.
6. Rutas de revisión y rechazo: compárelas con la aprobada (revisión inserta póliza pendiente sin cobro; rechazo solo la suscripción).
7. Amenazas a la validez: una sola zona, instancias t3 con créditos, dataset sintético, pasarela y firma fuera del camino medido, generador en la misma VPC.

### Conclusiones
Indique si la hipótesis se CONFIRMA o se INVALIDA para operación normal, con los números, y hasta qué nivel se sostiene.

### Decisión de arquitectura
Si se confirma: se ADOPTA la colocalización con transacción compartida para el núcleo de venta en la Fase 1, y se registra el punto de inflexión como límite que justifica escalar horizontalmente la API o separar servicios en la Fase 2. Si se invalida o el margen es pequeño: se AJUSTA, con candidatas ordenadas por costo (ajustar `DB_POOL_MAX` y repetir el nivel afectado; réplicas de la API detrás de un balanceador; pooler externo como PgBouncer). Explique implicaciones sobre otros atributos (la transacción atómica favorece disponibilidad e integridad de HU2.3.1; la colocalización limita la escalabilidad selectiva).

### Uso de IAG
Describa con honestidad qué partes se apoyaron en IAG (por ejemplo: revisión de coherencia del diseño contra los diagramas, generación inicial del código del refactor y de los scripts, redacción de borradores), qué verificó usted (compilación, pruebas locales, lectura del código, ejecución real en AWS), qué corrigió o decidió usted y qué propuestas descartó. Adjunte o enlace los prompts principales.

### Guion del video (máximo 5 minutos; explique con sus palabras, no lea)
0:00–0:40 Recordar el experimento: ASR HU2.1.1, hipótesis, tácticas y la escalera de niveles.
0:40–1:40 Consola de AWS: las tres instancias Running, grupos de seguridad y reglas, pestaña Monitoring.
1:40–2:40 Código: `SuscripcionService.decidir()` (transacción que llama a `PolizasService.emitir()` y `PagosService.cobrarPrima()`), entidad con `cotizacionId` único, script k6 y escalera.
2:40–3:40 Ejecución: `/health`, una corrida corta en vivo (por ejemplo operación normal) con k6 mostrando el resumen.
3:40–5:00 Resultados: tabla, figura de p95/p99, punto de inflexión, conclusión y decisión.
