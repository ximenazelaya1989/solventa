#!/usr/bin/env python3
"""Orquesta EXP-008 en AWS Academy (us-east-1) con boto3.

Usa las credenciales del Learner Lab (~/.aws/credentials o variables AWS_*).
La EC2 de JMeter se maneja por SSM, sin SSH. El estado (bucket, salidas del
stack) se guarda en estado.json junto a este script (no se sube al repo).

  python3 orquestar.py preparar                 # bucket S3 y codigo
  python3 orquestar.py desplegar --desired 0    # stack sin tareas
  python3 orquestar.py imagenes                 # build y push a ECR desde la EC2
  python3 orquestar.py desplegar --desired 1 --cuota false
  python3 orquestar.py sembrar                  # 10.000 perfiles
  python3 orquestar.py jmeter humo --rps 5
  python3 orquestar.py jmeter calibracion --desde 20 --paso 20 --hasta 200
  python3 orquestar.py corrida 1 --cuota false --c 100   # reinicio limpio + 14 min
  python3 orquestar.py metricas corrida_1
  python3 orquestar.py borrar
"""
import argparse
import io
import json
import secrets
import sys
import tarfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3

REGION = 'us-east-1'
STACK = 'exp008'
AQUI = Path(__file__).resolve().parent
EXP = AQUI.parent                       # docs/HU5.1.2-Daniela/experimento
RAIZ = EXP.parents[2]                   # raiz del repo
RESULTADOS = EXP.parent / 'resultados'  # docs/HU5.1.2-Daniela/resultados
ESTADO = AQUI / 'estado.json'

ses = boto3.Session(region_name=REGION)
cfn, ec2, s3, ssm, ecs, cw = (ses.client(x) for x in ('cloudformation', 'ec2', 's3', 'ssm', 'ecs', 'cloudwatch'))


def estado() -> dict:
    return json.loads(ESTADO.read_text()) if ESTADO.exists() else {}


def guardar(**kv):
    e = estado()
    e.update(kv)
    ESTADO.write_text(json.dumps(e, indent=2))


def log(msg: str):
    print(f'[{datetime.now():%H:%M:%S}] {msg}', flush=True)


# ------------------------------------------------------------------ preparar
def preparar(_):
    cuenta = ses.client('sts').get_caller_identity()['Account']
    vpc = ec2.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])['Vpcs'][0]['VpcId']
    subredes = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc]},
                                            {'Name': 'default-for-az', 'Values': ['true']}])['Subnets']
    por_az = {s['AvailabilityZone']: s['SubnetId'] for s in subredes}
    zonas = [z for z in ('us-east-1a', 'us-east-1b', 'us-east-1c', 'us-east-1d') if z in por_az][:2]
    e = estado()
    bucket = e.get('bucket') or f'exp008-{cuenta}-{secrets.token_hex(3)}'
    if 'bucket' not in e:
        s3.create_bucket(Bucket=bucket)
    guardar(cuenta=cuenta, vpc=vpc, subnet_a=por_az[zonas[0]], subnet_b=por_az[zonas[1]], bucket=bucket,
            db_password=e.get('db_password') or 'Exp008' + secrets.token_hex(8))
    subir_codigo(None)
    log(f'Cuenta {cuenta}, VPC {vpc}, zonas {zonas}, bucket {bucket}')


def subir_codigo(_):
    excluir = ('node_modules', 'dist', '__pycache__', '.tsbuildinfo', 'estado.json')
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as tar:
        for ruta in ('services/api-gateway', 'services/cotizacion', 'services/perfilamiento',
                     'docs/HU5.1.2-Daniela/experimento/carga', 'docs/HU5.1.2-Daniela/experimento/scripts'):
            tar.add(RAIZ / ruta, arcname=ruta, filter=lambda t: None if any(x in t.name for x in excluir) else t)
    s3.put_object(Bucket=estado()['bucket'], Key='codigo.tgz', Body=buf.getvalue())
    log(f'Codigo subido ({len(buf.getvalue()) // 1024} KB)')


# ----------------------------------------------------------------- stack
def desplegar(a):
    e = estado()
    params = {
        'VpcId': e['vpc'], 'SubnetA': e['subnet_a'], 'SubnetB': e['subnet_b'], 'DbPassword': e['db_password'],
        'DesiredCount': str(a.desired), 'RateLimitEnabled': a.cuota, 'RateLimitRps': str(a.rps),
        'RateLimitBurstS': str(a.rafaga),
    }
    plantilla = (EXP / 'infra' / 'exp008.yaml').read_text()
    kw = dict(StackName=STACK, TemplateBody=plantilla,
              Parameters=[{'ParameterKey': k, 'ParameterValue': v} for k, v in params.items()])
    try:
        cfn.describe_stacks(StackName=STACK)
        existe = True
    except cfn.exceptions.ClientError:
        existe = False
    if existe:
        try:
            cfn.update_stack(**kw)
        except cfn.exceptions.ClientError as err:
            if 'No updates are to be performed' in str(err):
                log('Stack sin cambios')
                return salidas()
            raise
        espera = 'stack_update_complete'
    else:
        cfn.create_stack(**kw, OnFailure='DO_NOTHING')
        espera = 'stack_create_complete'
    log(f'{"Actualizando" if existe else "Creando"} stack ({params["DesiredCount"]} tareas, cuota={a.cuota}, '
        f'{a.rps} rps)')
    cfn.get_waiter(espera).wait(StackName=STACK, WaiterConfig={'Delay': 15, 'MaxAttempts': 160})
    log('Stack listo')
    return salidas()


def salidas() -> dict:
    out = cfn.describe_stacks(StackName=STACK)['Stacks'][0].get('Outputs', [])
    o = {x['OutputKey']: x['OutputValue'] for x in out}
    guardar(salidas=o)
    return o


# ------------------------------------------------------------------- SSM
def ssm_correr(comandos: str, timeout_s: int = 3600, mostrar: bool = True) -> str:
    inst = estado()['salidas']['JMeterInstanceId']
    r = ssm.send_command(InstanceIds=[inst], DocumentName='AWS-RunShellScript',
                         Parameters={'commands': [comandos], 'executionTimeout': [str(timeout_s)]},
                         TimeoutSeconds=600)
    cid = r['Command']['CommandId']
    while True:
        time.sleep(5)
        try:
            inv = ssm.get_command_invocation(CommandId=cid, InstanceId=inst)
        except ssm.exceptions.InvocationDoesNotExist:
            continue
        if inv['Status'] in ('Success', 'Failed', 'Cancelled', 'TimedOut'):
            break
    salida = inv['StandardOutputContent'] + inv['StandardErrorContent']
    if mostrar:
        print(salida[-3000:])
    if inv['Status'] != 'Success':
        raise SystemExit(f'SSM terminó en {inv["Status"]}')
    return salida


def esperar_ssm():
    inst = estado()['salidas']['JMeterInstanceId']
    for _ in range(60):
        info = ssm.describe_instance_information(Filters=[{'Key': 'InstanceIds', 'Values': [inst]}])
        if info['InstanceInformationList']:
            return
        time.sleep(10)
    raise SystemExit('La EC2 no se registró en SSM')


def entorno() -> str:
    e = estado()
    o = e['salidas']
    return (f"export B={e['bucket']} ALB={o['AlbPublicoDns']} INT={o['AlbInternoDns']} "
            f"COT_DB={o['CotizacionBDHost']} PERF_DB={o['PerfilamientoBDHost']} REDIS={o['RedisHost']} "
            f"PGPASSWORD={e['db_password']} REG={e['cuenta']}.dkr.ecr.{REGION}.amazonaws.com; "
            "cd /opt/exp008; ")


def imagenes(_):
    esperar_ssm()
    log('Esperando la instalación de la EC2, construyendo y publicando imágenes')
    ssm_correr(entorno() + """
set -e
for i in $(seq 90); do [ -f /opt/exp008/LISTO ] && break; sleep 10; done
aws s3 cp s3://$B/codigo.tgz . --quiet && rm -rf src && mkdir src && tar xzf codigo.tgz -C src
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $REG >/dev/null
for s in api-gateway cotizacion perfilamiento; do
  docker build -q -t $REG/exp008-$s:exp008 src/services/$s
  docker push -q $REG/exp008-$s:exp008
done
docker images | grep exp008
""", timeout_s=2400)


def sembrar(_):
    log('Sembrando 10.000 perfiles por POST /perfiles')
    ssm_correr(entorno() + 'python3 src/docs/HU5.1.2-Daniela/experimento/carga/sembrar_perfiles.py http://$INT:8002 10000',
               timeout_s=1800)


# ------------------------------------------------------------- JMeter
def jmeter(a, nombre: str | None = None) -> dict:
    nombre = nombre or a.tipo
    args = {'corrida': f'--c {a.c}', 'calibracion': f'--desde {a.desde} --paso {a.paso} --hasta {a.hasta}',
            'humo': f'--rps {a.rps}'}[a.tipo]
    log(f'JMeter {a.tipo} ({args}) -> {nombre}.jtl')
    inicio = datetime.now(timezone.utc)
    ssm_correr(entorno() + f"""
set -e
mkdir -p res && rm -f res/{nombre}.jtl
python3 src/docs/HU5.1.2-Daniela/experimento/carga/generar_plan.py {a.tipo} {args} --salida res/{nombre}.jmx
HEAP="-Xms1g -Xmx4g" jmeter -n -t res/{nombre}.jmx -Jhost=$ALB -Jport=80 -l res/{nombre}.jtl -j res/{nombre}.log \
  -Jjmeter.save.saveservice.output_format=csv > res/{nombre}.out 2>&1
tail -3 res/{nombre}.out
gzip -kf res/{nombre}.jtl && aws s3 cp res/{nombre}.jtl.gz s3://$B/res/ --quiet
aws s3 cp res/{nombre}.jmx s3://$B/res/ --quiet
""", timeout_s=3600)
    fin = datetime.now(timezone.utc)
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    import gzip
    cuerpo = s3.get_object(Bucket=estado()['bucket'], Key=f'res/{nombre}.jtl.gz')['Body'].read()
    (RESULTADOS / f'{nombre}.jtl').write_bytes(gzip.decompress(cuerpo))
    s3.download_file(estado()['bucket'], f'res/{nombre}.jmx', str(RESULTADOS / f'{nombre}.jmx'))
    reg = {'nombre': nombre, 'inicio': inicio.isoformat(), 'fin': fin.isoformat()}
    log(f'{nombre} terminado y descargado')
    return reg


# ------------------------------------------------------------ corridas
def reinicio_limpio():
    """Vacia las cotizaciones y el Redis y reinicia las tres tareas."""
    ssm_correr(entorno() + """
psql -h $COT_DB -U postgres -d cotizacion_db -c 'TRUNCATE cotizaciones' 2>&1 | tail -1
redis6-cli -h $REDIS FLUSHALL
""")
    cluster = estado()['salidas']['ClusterName']
    servicios = ['api-gateway', 'cotizacion', 'perfilamiento']
    for s in servicios:
        ecs.update_service(cluster=cluster, service=s, forceNewDeployment=True)
    log('Reinicio de las tres tareas solicitado')
    time.sleep(20)
    ecs.get_waiter('services_stable').wait(cluster=cluster, services=servicios,
                                           WaiterConfig={'Delay': 15, 'MaxAttempts': 80})
    ssm_correr(entorno() + 'for i in $(seq 30); do curl -sf http://$ALB/health >/dev/null && break; sleep 5; done; '
               'curl -s http://$ALB/health', mostrar=True)
    time.sleep(30)  # que el ALB termine de marcar sanos los destinos


def corrida(a):
    e = estado()
    ns = argparse.Namespace(desired=1, cuota=a.cuota, rps=a.rps, rafaga=a.rafaga)
    if e.get('cuota_actual') != [a.cuota, a.rps]:
        desplegar(ns)
        guardar(cuota_actual=[a.cuota, a.rps])
    reinicio_limpio()
    a.tipo = 'corrida'
    reg = jmeter(a, nombre=f'corrida_{a.n}_{"con" if a.cuota == "true" else "sin"}')
    reg.update(n=a.n, cuota=a.cuota == 'true', c=a.c, cuota_rps=a.rps, rafaga_s=a.rafaga)
    corridas = [x for x in estado().get('corridas', []) if x['n'] != a.n] + [reg]
    guardar(corridas=sorted(corridas, key=lambda x: x['n']))
    (RESULTADOS / 'corridas.json').write_text(json.dumps({
        'C': a.c, 'cuota_rps': a.rps, 'rafaga_s': a.rafaga,
        'corridas': [{'n': x['n'], 'cuota': x['cuota'], 'jtl': x['nombre'] + '.jtl',
                      'inicio': x['inicio'], 'fin': x['fin']} for x in sorted(corridas, key=lambda x: x['n'])],
    }, indent=1))
    metricas(argparse.Namespace(nombre=reg['nombre'], inicio=reg['inicio'], fin=reg['fin']))


# -------------------------------------------------------------- metricas
def metricas(a):
    e = estado()
    o = e['salidas']
    reg = next((x for x in e.get('corridas', []) if x['nombre'] == a.nombre), None)
    inicio = datetime.fromisoformat(a.inicio or reg['inicio']) - timedelta(minutes=1)
    fin = datetime.fromisoformat(a.fin or reg['fin']) + timedelta(minutes=1)
    consultas, i = [], 0

    def q(ns, metrica, dims, stat='Average'):
        nonlocal i
        i += 1
        consultas.append({'Id': f'm{i}', 'Label': f'{metrica}|{"|".join(v for _, v in dims)}', 'MetricStat': {
            'Metric': {'Namespace': ns, 'MetricName': metrica,
                       'Dimensions': [{'Name': k, 'Value': v} for k, v in dims]},
            'Period': 60, 'Stat': stat}})

    for s in ('api-gateway', 'cotizacion', 'perfilamiento'):
        for m in ('CPUUtilization', 'MemoryUtilization'):
            q('AWS/ECS', m, [('ClusterName', o['ClusterName']), ('ServiceName', s)])
            q('AWS/ECS', m, [('ClusterName', o['ClusterName']), ('ServiceName', s)], 'Maximum')
    for bd in (o['CotizacionBDId'], o['PerfilamientoBDId']):
        for m in ('CPUUtilization', 'DatabaseConnections'):
            q('AWS/RDS', m, [('DBInstanceIdentifier', bd)], 'Maximum')
    q('AWS/ElastiCache', 'CPUUtilization', [('CacheClusterId', o['RedisId'])], 'Maximum')
    q('AWS/EC2', 'CPUUtilization', [('InstanceId', o['JMeterInstanceId'])], 'Maximum')
    r = cw.get_metric_data(MetricDataQueries=consultas, StartTime=inicio, EndTime=fin)
    datos = {m['Label'] + '|' + c['MetricStat']['Stat']: {
        'ts': [t.isoformat() for t in m['Timestamps']], 'valores': m['Values']}
        for m, c in zip(r['MetricDataResults'], consultas)}
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    (RESULTADOS / f'cloudwatch_{a.nombre}.json').write_text(json.dumps(datos, indent=1))
    for k, v in datos.items():
        if v['valores']:
            print(f'{k:70s} max={max(v["valores"]):.1f}')


def borrar(_):
    e = estado()
    log('Borrando el stack')
    cfn.delete_stack(StackName=STACK)
    cfn.get_waiter('stack_delete_complete').wait(StackName=STACK, WaiterConfig={'Delay': 20, 'MaxAttempts': 120})
    if e.get('bucket'):
        b = boto3.resource('s3', region_name=REGION).Bucket(e['bucket'])
        b.objects.all().delete()
        b.delete()
    log('Todo borrado')


# ------------------------------------------- modo asincrono (runner en la EC2)
# Las corridas largas las ejecuta runner_ec2.sh en la EC2 (rol LabRole), asi no
# dependen de que la maquina que orquesta siga conectada.
def escribir_env():
    e = estado()
    o = e['salidas']
    env = (f"export B={e['bucket']} ALB={o['AlbPublicoDns']} INT={o['AlbInternoDns']} "
           f"COT_DB={o['CotizacionBDHost']} PERF_DB={o['PerfilamientoBDHost']} REDIS={o['RedisHost']} "
           f"PGPASSWORD={e['db_password']} REG={e['cuenta']}.dkr.ecr.{REGION}.amazonaws.com "
           f"CLUSTER={o['ClusterName']} TD_SIN={e.get('td_sin', '')} TD_CON={e.get('td_con', '')}")
    ssm_correr(f"mkdir -p /opt/exp008/res && echo '{env}' > /opt/exp008/env.sh", mostrar=False)


def lanzar(a):
    escribir_env()
    # src/ se crea con 'lanzar imagenes' (el runner descarga codigo.tgz del bucket)
    ssm_correr(entorno() + 'mkdir -p res; [ -d src ] || { aws s3 cp s3://$B/codigo.tgz . && mkdir -p src '
               '&& tar xzf codigo.tgz -C src; }; '
               f'setsid nohup bash src/docs/HU5.1.2-Daniela/experimento/scripts/runner_ec2.sh {a.accion} '
               f'{" ".join(a.args)} > res/runner_{a.accion}.out 2>&1 < /dev/null & sleep 3; echo lanzado',
               timeout_s=120)


def ver_progreso(_):
    try:
        print(s3.get_object(Bucket=estado()['bucket'], Key='res/progreso.log')['Body'].read().decode()[-2500:])
    except s3.exceptions.NoSuchKey:
        print('sin progreso todavia')


def registrar_td(a):
    """Registra la task definition del gateway con cuota (0,2C) y guarda la de control."""
    e = estado()
    o = e['salidas']
    actual = ecs.describe_services(cluster=o['ClusterName'], services=['api-gateway'])['services'][0]['taskDefinition']
    td = ecs.describe_task_definition(taskDefinition=actual)['taskDefinition']
    base = {k: td[k] for k in ('family', 'containerDefinitions', 'cpu', 'memory', 'networkMode',
                               'requiresCompatibilities', 'executionRoleArn', 'taskRoleArn')}

    def con_flag(valor: str, rps: float) -> str:
        cd = json.loads(json.dumps(base['containerDefinitions']))
        for v in cd[0]['environment']:
            if v['name'] == 'REDIS_URL':
                v['value'] = f"redis://{o['RedisHost']}:6379/0"
            if v['name'] == 'RATE_LIMIT_ENABLED':
                v['value'] = valor
            if v['name'] == 'RATE_LIMIT_RPS':
                v['value'] = f'{rps:g}'
        return ecs.register_task_definition(**{**base, 'containerDefinitions': cd})['taskDefinition']['taskDefinitionArn']

    rps = round(0.2 * a.c, 1)
    guardar(td_sin=con_flag('false', rps), td_con=con_flag('true', rps), C=a.c, cuota_rps=rps)
    print(json.dumps({k: estado()[k] for k in ('td_sin', 'td_con', 'C', 'cuota_rps')}, indent=1))


def descargar(_):
    import gzip
    e = estado()
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    objs = s3.list_objects_v2(Bucket=e['bucket'], Prefix='res/').get('Contents', [])
    for ob in objs:
        nombre = ob['Key'].split('/', 1)[1]
        cuerpo = s3.get_object(Bucket=e['bucket'], Key=ob['Key'])['Body'].read()
        if nombre.endswith('.jtl.gz'):
            (RESULTADOS / nombre[:-3]).write_bytes(gzip.decompress(cuerpo))
            (RESULTADOS / 'crudos').mkdir(exist_ok=True)
            (RESULTADOS / 'crudos' / nombre).write_bytes(cuerpo)
        else:
            (RESULTADOS / 'crudos').mkdir(exist_ok=True)
            (RESULTADOS / 'crudos' / nombre).write_bytes(cuerpo)
    corridas = []
    for n, m in ((1, 'sin'), (2, 'con'), (3, 'sin'), (4, 'con'), (5, 'sin'), (6, 'con')):
        nombre = f'corrida_{n}_{m}'
        if (RESULTADOS / f'{nombre}.jtl').exists() and (RESULTADOS / 'crudos' / f'{nombre}.fin').exists():
            corridas.append({'n': n, 'cuota': m == 'con', 'jtl': f'{nombre}.jtl', 'nombre': nombre,
                             'inicio': (RESULTADOS / 'crudos' / f'{nombre}.inicio').read_text().strip(),
                             'fin': (RESULTADOS / 'crudos' / f'{nombre}.fin').read_text().strip()})
    (RESULTADOS / 'corridas.json').write_text(json.dumps({
        'C': e.get('C'), 'cuota_rps': e.get('cuota_rps'), 'rafaga_s': 2, 'corridas': corridas}, indent=1))
    for c in corridas:
        metricas(argparse.Namespace(nombre=c['nombre'], inicio=c['inicio'].replace('Z', '+00:00'),
                                    fin=c['fin'].replace('Z', '+00:00')))
    log(f'{len(objs)} archivos descargados, {len(corridas)} corridas')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest='cmd', required=True)
    sp.add_parser('preparar').set_defaults(f=preparar)
    sp.add_parser('subir-codigo').set_defaults(f=subir_codigo)
    d = sp.add_parser('desplegar')
    d.add_argument('--desired', type=int, default=1)
    d.add_argument('--cuota', default='false')
    d.add_argument('--rps', type=float, default=20)
    d.add_argument('--rafaga', type=float, default=2)
    d.set_defaults(f=lambda a: print(json.dumps(desplegar(a), indent=1)))
    sp.add_parser('imagenes').set_defaults(f=imagenes)
    sp.add_parser('sembrar').set_defaults(f=sembrar)
    j = sp.add_parser('jmeter')
    j.add_argument('tipo', choices=['humo', 'calibracion'])
    j.add_argument('--rps', type=float, default=5)
    j.add_argument('--desde', type=int, default=20)
    j.add_argument('--paso', type=int, default=20)
    j.add_argument('--hasta', type=int, default=200)
    j.set_defaults(f=jmeter)
    c = sp.add_parser('corrida')
    c.add_argument('n', type=int)
    c.add_argument('--cuota', choices=['true', 'false'], required=True)
    c.add_argument('--c', type=float, required=True)
    c.add_argument('--rps', type=float, help='cuota por socio (por defecto 0,2C)')
    c.add_argument('--rafaga', type=float, default=2)
    c.set_defaults(f=lambda a: corrida(a) if a.rps else (setattr(a, 'rps', round(0.2 * a.c, 1)) or corrida(a)))
    m = sp.add_parser('metricas')
    m.add_argument('nombre')
    m.add_argument('--inicio')
    m.add_argument('--fin')
    m.set_defaults(f=metricas)
    s = sp.add_parser('ssm')
    s.add_argument('comando')
    s.set_defaults(f=lambda a: ssm_correr(entorno() + a.comando))
    sp.add_parser('borrar').set_defaults(f=borrar)
    la = sp.add_parser('lanzar')
    la.add_argument('accion', choices=['imagenes', 'sembrar', 'humo', 'calibrar', 'corridas', 'demo'])
    la.add_argument('args', nargs='*')
    la.set_defaults(f=lanzar)
    sp.add_parser('progreso').set_defaults(f=ver_progreso)
    rt = sp.add_parser('registrar-td')
    rt.add_argument('--c', type=float, required=True)
    rt.set_defaults(f=registrar_td)
    sp.add_parser('descargar').set_defaults(f=descargar)
    a = p.parse_args()
    a.f(a)
