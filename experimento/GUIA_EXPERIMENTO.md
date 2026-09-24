# Experimento HU2.1.1 · Colocalización de Suscripción, Pólizas y Pagos en la decisión y emisión automática

Guía en cuatro partes: (0) estado del código, (1) texto de Planeación registrado en Hélix, (2) procedimiento de ejecución con la consola de AWS, (3) documento de resultados, video y entrega. Sigue la estructura de `Lab3_Diseño_del_experimentov3.pdf` y `Lab3_Ejecucion_del_experimentov2.pdf`.

---

## PARTE 0 · Estado del código (listo y verificado)

Rama de trabajo: `feature/experimento-hu211`, creada desde `feature/refactor-12-modulos` (base común de 12 módulos; ver `CLAUDE.md` en la raíz). Cuando ambas ramas se fusionen a `main`, use `main` en todos los comandos de clonación de la Parte 2.

Lo que ya está implementado y verificado localmente con Docker:

1. `POST /suscripciones` con cuerpo `{ "cotizacionId": "<uuid>" }` responde 201 con `id`, `decision`, `polizaId` e `idempotente`; cotización inexistente → 404; campos extra (por ejemplo `score`) → 400. `GET /suscripciones/:id` → 200 o 404.
2. Decisión por umbrales sobre el score del PerfilRiesgo de la cotización (`Cotizacion.perfilRiesgoId`), configurables con `SUSCRIPCION_UMBRAL_APROBACION` (0.7) y `SUSCRIPCION_UMBRAL_REVISION` (0.4). Valores que devuelve la API: `aprobado`, `revision_asistida`, `rechazado`.
3. Rutas, todas dentro de una sola transacción:
   - `aprobado`: suscripción + póliza emitida con su pago `cobro_prima` pendiente (`PolizasService.emitir()`, que llama internamente a `PagosService.cobrarPrima()`).
   - `revision_asistida`: suscripción + póliza pendiente (`PolizasService.registrarPendiente()`), sin cobro.
   - `rechazado`: solo la suscripción.
4. Idempotencia: 10 peticiones concurrentes con la misma cotización → 10 respuestas 201 (una con `idempotente: false`), cero errores y en la BD 1 suscripción, 1 póliza y 1 pago.
5. Kit `experimento/` adaptado al esquema real. La semilla usa las etiquetas `aprobada`, `revision` y `rechazada` en la columna `esperado` del CSV; `k6/suscripcion.js` las traduce a los valores de la API antes de comparar.

Antes de fusionar a `main`, coordine con el compañero dueño de la rama `feature/hu112-rolling-update-reglas-rating`, porque el refactor modifica `src/cotizacion` (este kit no la toca).

---

## PARTE 1 · Planeación (texto registrado en Hélix)

### Hipótesis de diseño
Decisión arquitectónica bajo prueba: la decisión de suscripción y la emisión de la póliza se implementan como invocaciones en-proceso entre los módulos Suscripción, Pólizas y Pagos del monolito modular, dentro de una sola transacción que guarda la suscripción, la póliza y el cobro de la prima.

Hipótesis (H1), latencia: bajo este enfoque colocalizado, la decisión y la emisión de una solicitud que cumple el perfil de riesgo cumplirán el ASR de HU2.1.1 (p95 ≤ 1,5 s y p99 ≤ 3 s) en operación normal (50 TPS), con menos de 1 % de errores, y se mantendrán dentro del umbral hasta un nivel de carga identificable, a partir del cual la latencia crecerá de forma no lineal.

Alcance: el experimento evalúa si el diseño colocalizado es suficiente para cumplir el ASR; no lo compara con una variante HTTP. La pasarela de pago y la firma electrónica quedan fuera del camino medido: el cobro queda en estado pendiente y se procesa después. Los 50 TPS son un supuesto del equipo: unas 833 cotizaciones por segundo en campaña con una conversión cercana al 6 %.

### Tácticas y patrones
Táctica principal, localización de recursos (colocalización): Suscripción, Pólizas y Pagos se comunican por invocación directa de métodos dentro del mismo proceso, sin saltos de red.
¿Por qué esta táctica y no otra? Separarlos en servicios añadiría saltos de red y exigiría una transacción distribuida para no dejar pólizas sin cobro. El caso reserva esa separación para la Fase 2.

Tácticas de soporte: una transacción atómica, para que no queden pólizas sin cobro (HU2.3.1); idempotencia por unicidad de `cotizacionId`, para que un reintento no duplique la póliza; y un pool de conexiones acotado (`DB_POOL_MAX`), que limita la carga sobre PostgreSQL.
¿Por qué estas y no otras? Son las que exige el modelo de concurrencia y funcionan aunque la API tenga varias réplicas, a diferencia de un bloqueo en memoria.

Táctica secundaria, reducción de overhead: la decisión compara umbrales sobre el score del PerfilRiesgo ya calculado, sin recalcularlo. Se reporta en el análisis como factor que contribuye, no como hipótesis propia.

### Diseño del experimento
Variable independiente: la tasa de llegada (TPS), en una escalera con k6: 2 (smoke), 10, 25, 50 (operación normal), 100, 200 y 400 TPS (estrés), con corridas de 180 s, 8 repeticiones en operación normal y estrés, y 4 en los demás niveles.

Variables dependientes: p95, p99, promedio, mínimo, máximo y desviación estándar de la latencia de las solicitudes aprobadas en `POST /suscripciones`, además del throughput logrado y la tasa de error. Una corrida cumple el ASR solo si además tiene menos de 1 % de errores.

Variables controladas: las mismas tres instancias EC2 y la misma configuración (pool de 10 conexiones, umbrales 0,7 y 0,4). La base de datos se reinicia y se vuelve a sembrar antes de cada corrida, con una cotización nueva por solicitud y la misma distribución de scores (70 % aprobación, 20 % revisión, 10 % rechazo). Entre corridas hay 60 s de enfriamiento, y el batch de perfiles se mantiene apagado.

Software: el endpoint `POST /suscripciones` con la transacción en-proceso, el script SQL de semilla, el script de k6 por niveles, el script de escalera y el de consolidación de resultados.

Procedimiento:
1. Iniciar el Learner Lab y crear en la consola de EC2 los grupos de seguridad y tres instancias en la misma zona: `solventa-app`, `solventa-db` y `solventa-loadgen`.
2. Levantar PostgreSQL en `solventa-db` y una instancia de la API en `solventa-app` con los archivos de `experimento/docker`.
3. Verificar `/health` desde `solventa-loadgen` y ejecutar el smoke test para validar el circuito.
4. Ejecutar la escalera completa, observando la pestaña Monitoring de las instancias.
5. Consolidar las corridas por nivel y determinar el punto de inflexión: el mayor nivel que cumple el ASR.
6. Recolectar la evidencia, terminar las instancias, borrar los grupos de seguridad y revisar Cost Explorer.

### Recursos requeridos
AWS Academy Learner Lab, en la región us-east-1, con tres instancias Ubuntu 24.04 en la misma zona: `solventa-app` (t3.medium), con la API en Docker; `solventa-db` (t3.medium), con PostgreSQL 16, separada según la vista de despliegue; y `solventa-loadgen` (t3.small), con k6, dentro de la VPC para no medir la latencia de red desde Bogotá ni competir por CPU con la API. Se necesitan también grupos de seguridad para SSH, el puerto 3000 y el puerto 5432, el par de llaves `vockey`, el repositorio con la carpeta `experimento`, Python para consolidar y una hoja de cálculo. El costo aproximado es de USD 0,10 por hora.

### Elementos de arquitectura involucrados
Componentes: Suscripción, Pólizas y Pagos, con lectura de Cotización y Perfilamiento. Clases: Suscripcion, Poliza, Pago, Cotizacion y PerfilRiesgo. Conector: invocación en-proceso con transacción compartida. Concurrencia: el hilo del núcleo de venta y el semáforo de conexiones. Despliegue: nodo de aplicación y capa de datos separados.

### Esfuerzo estimado
12 horas-persona, distribuidas así: 2 horas para el endpoint y la transacción, 2 horas para el script de carga y la semilla de datos, 1,5 horas para el aprovisionamiento en AWS, 3 horas para la ejecución de la escalera de niveles, 1,5 horas para la consolidación de resultados y la determinación del punto de inflexión, y 2 horas para la documentación y el video.

---

## PARTE 2 · Ejecución paso a paso en AWS

Antes de empezar: reserve una sesión continua de unas 4 horas; tenga a mano la URL del repositorio (confírmela con `git remote -v` en su equipo) y, si es privado, un *personal access token* de GitHub con permiso de lectura. Tenga abierto un archivo de notas para anotar IPs y la hora de inicio y fin de cada fase (esfuerzo real). Tome captura de cada paso marcado con 📸.

En los comandos, `<URL_REPO>` es la URL del repositorio (por ejemplo `https://github.com/ximenazelaya1989/solventa.git`; si es privado, `https://<TOKEN>@github.com/ximenazelaya1989/solventa.git`) y `<RAMA>` es `feature/experimento-hu211` (o `main` cuando ya esté fusionada).

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
Para cada una: AMI **Ubuntu Server 24.04 LTS**, Key pair **vockey**, en *Network settings* clic en **Edit** y elija la **misma subnet** (por ejemplo, la de us-east-1a) para las tres, *Select existing security group*, almacenamiento 20 GiB gp3. En *Advanced details*: **Credit specification = Unlimited** y pegue el contenido del *User data* indicado (ábralo desde el repositorio en VS Code y cópielo completo).

| Nombre | Tipo | Security group | User data |
|---|---|---|---|
| solventa-db | t3.medium | sg-solventa-db | `experimento/infra/user-data-docker.sh` |
| solventa-app | t3.medium | sg-solventa-app | `experimento/infra/user-data-docker.sh` |
| solventa-loadgen | t3.small | sg-solventa-loadgen | `experimento/infra/user-data-loadgen.sh` |

Opcional pero recomendado: en la instancia seleccionada, *Actions >> Monitor and troubleshoot >> Manage detailed monitoring >> Enable* (métricas cada minuto en lugar de cada cinco).

Anote para cada instancia la **IP pública** (para SSH) y la **IP privada** (para el tráfico entre ellas). 📸 Lista de instancias en estado *Running* con *Status check 2/2*.

Espere unos 3 minutos y, al entrar por SSH a cada una, verifique que el user data terminó: `ls ~/user-data-ok` debe existir.

### 2.4 Base de datos (SSH a solventa-db)
```powershell
ssh -i $HOME\.ssh\labsuser.pem ubuntu@<IP_PUBLICA_DB>
```
```bash
git clone <URL_REPO> solventa
cd solventa && git checkout <RAMA>
cd experimento/docker
sudo docker compose -f docker-compose.db.yml up -d
sudo docker ps          # 📸 contenedor postgres:16 "Up"
```

### 2.5 Aplicación (SSH a solventa-app)
```bash
git clone <URL_REPO> solventa
cd solventa && git checkout <RAMA>
cp experimento/.env.experimento.example experimento/.env.experimento
sed -i 's/^DB_HOST=.*/DB_HOST=<IP_PRIVADA_DB>/' experimento/.env.experimento
cd experimento/docker
sudo docker compose -f docker-compose.app.yml up -d --build   # 3-5 min la primera vez
sudo docker compose -f docker-compose.app.yml logs --tail 30  # debe decir que Nest arrancó
curl http://localhost:3000/health                            # {"status":"ok"}
```
La API crea las tablas al arrancar (`DB_SYNCHRONIZE=true`, solo en este entorno desechable). Déjela corriendo. No use el `docker-compose.yml` de la raíz: levanta réplicas y un balanceador, que no forman parte de este experimento. Para observar recursos durante las corridas: `sudo docker stats`.

### 2.6 Generador de carga (SSH a solventa-loadgen)
```bash
git clone <URL_REPO> solventa
cd solventa && git checkout <RAMA>
cd experimento && chmod +x scripts/correr-escalera.sh
mkdir -p resultados
export BASE_URL=http://<IP_PRIVADA_APP>:3000
export DB_HOST=<IP_PRIVADA_DB>
curl $BASE_URL/health                                         # 📸
```
La semilla se ejecuta desde aquí con `psql` contra la IP privada de la base, y el archivo `seed/cotizaciones.csv` queda en esta instancia, que es donde k6 lo lee.

### 2.7 Smoke test
```bash
./scripts/correr-escalera.sh smoke
cat resultados/smoke-rep1.json
```
Verifique en el JSON: `tasaError` = 0, `decisionesInesperadas` = 0, y conteos por decisión cercanos a 70/20/10 %. Si hay decisiones inesperadas, el batch de perfiles se ejecutó o la semilla no corrió: no siga hasta corregirlo. 📸 Salida del smoke.

### 2.8 Escalera completa (dentro de tmux, para que no se corte si se cae el SSH)
```bash
tmux new -s escalera
cd ~/solventa/experimento
export BASE_URL=http://<IP_PRIVADA_APP>:3000
export DB_HOST=<IP_PRIVADA_DB>
./scripts/correr-escalera.sh 2>&1 | tee resultados/escalera.log
# Salir sin detener: Ctrl+B y luego D.  Volver: tmux attach -t escalera
```
Duración aproximada 2,5 h. Mientras corre:
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
Resultado: `analisis/tabla-resultados.csv` y las figuras `fig-latencia.png`, `fig-error.png`, `fig-throughput.png`; en consola se imprime el punto de inflexión. Haga commit de `resultados/` y `analisis/` (son evidencia). Descargue los resultados **antes** de terminar las instancias.

### 2.10 Limpieza (obligatoria)
1. EC2 >> Instances >> seleccione las tres >> *Instance state >> Terminate*. Espere *Terminated*. 📸
2. EC2 >> Volumes: verifique que no quedan volúmenes *available* (si queda alguno, *Delete*).
3. Security Groups: borre `sg-solventa-db`, luego `sg-solventa-app`, luego `sg-solventa-loadgen`.
4. 📸 Cost Explorer con el costo final del experimento (puede tardar horas en reflejarse; tome la captura al día siguiente si hace falta).
5. Vocareum >> **End Lab**.
6. Si usó un token de GitHub, revóquelo al terminar (GitHub >> Settings >> Developer settings >> Personal access tokens).

---

## PARTE 3 · Documento de resultados, video y entrega

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
7. Amenazas a la validez: una sola zona, instancias t3 con créditos, dataset sintético, pasarela y firma fuera del camino medido, generador en la misma VPC, y que no se comparó con una variante HTTP.

Para justificar las tácticas con más profundidad que en Hélix: separar en servicios obligaría a una saga o a un compromiso en dos fases para no dejar pólizas sin cobro; tres escrituras independientes violarían HU2.3.1; un bloqueo en memoria no sobrevive a varias réplicas ni a reintentos, mientras que la unicidad en la base sí; y un pool ilimitado traslada la contención a PostgreSQL y degrada la latencia de cola de forma impredecible, mientras que uno acotado la convierte en espera medible dentro de la API.

### Conclusiones
Indique si la hipótesis se CONFIRMA o se INVALIDA para operación normal, con los números, y hasta qué nivel se sostiene.

### Decisión de arquitectura
Si se confirma: se ADOPTA la colocalización con transacción compartida para el núcleo de venta en la Fase 1, y se registra el punto de inflexión como límite que justifica escalar horizontalmente la API o separar servicios en la Fase 2. Si se invalida o el margen es pequeño: se AJUSTA, con candidatas ordenadas por costo (ajustar `DB_POOL_MAX` y repetir el nivel afectado; réplicas de la API detrás de un balanceador; pooler externo como PgBouncer). Explique implicaciones sobre otros atributos (la transacción atómica favorece la integridad de HU2.3.1; la colocalización limita la escalabilidad selectiva).

### Uso de IAG
Describa con honestidad qué partes se apoyaron en IAG (revisión de coherencia del diseño contra los diagramas, código del refactor y del endpoint generado con Claude Code, scripts del kit, borradores de texto), qué verificó usted (lectura de cada commit, compilación, pruebas locales con Docker, ejecución real en AWS), qué corrigió o decidió usted (por ejemplo, el destino de ReporteRegulatorio, no versionar `tsbuildinfo`, encapsular la póliza pendiente en `PolizasService`, alcance mínimo en módulos ajenos) y qué propuestas descartó. Los commits con `Co-Authored-By` sirven de evidencia. Adjunte o enlace los prompts principales.

### Guion del video (máximo 5 minutos; explique con sus palabras, no lea)
0:00–0:40 Recordar el experimento: ASR HU2.1.1, hipótesis, tácticas y la escalera de niveles.
0:40–1:40 Consola de AWS: las tres instancias Running, grupos de seguridad y reglas, pestaña Monitoring.
1:40–2:40 Código: `SuscripcionService.decidir()` abre la transacción y llama a `PolizasService.emitir()` o `registrarPendiente()`; `emitir()` llama a `PagosService.cobrarPrima()`. `cotizacionId` único, script k6 y escalera.
2:40–3:40 Ejecución: `/health`, una corrida corta en vivo (por ejemplo operación normal) con k6 mostrando el resumen.
3:40–5:00 Resultados: tabla, figura de p95/p99, punto de inflexión, conclusión y decisión.

Grabe el video mientras las instancias siguen encendidas (antes de la limpieza), o al menos la parte de la consola y de la ejecución.

### Entrega y registro en Hélix
1. Guarde el informe como `experimento/informe/HU211-resultados.pdf` y el video como `experimento/informe/HU211-video.mp4` (menos de 100 MB: expórtelo en 720p o comprímalo), haga commit y push.
2. Hélix >> Proyecto >> Arquitectura de Software >> pestaña Experimentos >> su experimento >> Resultados y análisis >> Enlaces y evidencias >> **Informe externo**: URL del PDF en GitHub.
3. En la misma sección, **+ Agregar evidencia**: URL del video en GitHub.
4. Verifique que los enlaces abran para alguien que no sea usted (los profesores deben tener acceso al repositorio) y, una vez fusionado, que apunten a `main`.
5. Prepare la argumentación del espacio sincrónico: pantalla y rostro, explicando sin leer el ASR, la decisión apoyada en una vista, el diseño, el análisis y la conclusión.