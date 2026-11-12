#!/usr/bin/env bash
# EXP-007 · Paso 4: copia el script de medicion y el plan de JMeter a la EC2 de carga,
# abre una sesion SSH o trae los resultados de vuelta al repo.
# La llave se descarga del Learner Lab (AWS Details > Download PEM) a ~/Downloads/labsuser.pem
# (otra ruta: LLAVE=/ruta/labsuser.pem ./04-ec2.sh ...).
#
#   ./04-ec2.sh subir     copia medicion/ y jmeter/ a ~/exp007 en la EC2
#   ./04-ec2.sh ssh       abre una sesion en la EC2
#   ./04-ec2.sh traer     baja ~/exp007/medicion/resultados a docs/HU3.2.1-Diego/medicion/resultados
source "$(dirname "$0")/comun.sh"
ACCION="${1:-}"
verificar_credenciales
[ -f "$LLAVE" ] || { rojo "No encuentro la llave $LLAVE (Learner Lab > AWS Details > Download PEM)"; exit 1; }
chmod 400 "$LLAVE"
IP=$(ip_ec2)
[ -n "$IP" ] && [ "$IP" != "None" ] || { rojo "No encontre la EC2 de carga encendida (¿Lab apagado o pila sin desplegar?)"; exit 1; }
SSH_OPC="-i $LLAVE -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
azul "EC2 de carga: $IP"

case "$ACCION" in
  subir)
    # shellcheck disable=SC2086
    ssh $SSH_OPC "ec2-user@$IP" "mkdir -p ~/exp007/medicion ~/exp007/jmeter"
    # shellcheck disable=SC2086
    scp $SSH_OPC "$EXP/medicion/medir_revocacion.py" "$EXP/medicion/requirements.txt" "ec2-user@$IP:~/exp007/medicion/"
    # shellcheck disable=SC2086
    scp $SSH_OPC "$EXP/jmeter/carga_fondo.jmx" "ec2-user@$IP:~/exp007/jmeter/"
    # shellcheck disable=SC2086
    if ssh $SSH_OPC "ec2-user@$IP" "test -f ~/LISTO"; then
      verde "Archivos copiados y la EC2 ya termino de instalar JMeter. Conectate con: ./04-ec2.sh ssh"
    else
      azul "Archivos copiados. La EC2 aun esta instalando JMeter (2-3 min tras crearse); espera a que exista ~/LISTO."
    fi
    ;;
  ssh)
    # shellcheck disable=SC2086
    exec ssh $SSH_OPC "ec2-user@$IP"
    ;;
  traer)
    mkdir -p "$EXP/medicion/resultados"
    # shellcheck disable=SC2086
    scp -r $SSH_OPC "ec2-user@$IP:~/exp007/medicion/resultados/." "$EXP/medicion/resultados/"
    verde "Resultados en $EXP/medicion/resultados"
    ;;
  *)
    rojo "Uso: $0 subir | ssh | traer"; exit 1 ;;
esac
