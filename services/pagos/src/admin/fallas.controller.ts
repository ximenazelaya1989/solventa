import {
  Controller,
  ForbiddenException,
  Headers,
  HttpCode,
  NotFoundException,
  Post,
} from '@nestjs/common';
import { instancia } from '../common/instancia';

// EXP-006 (H7.2.1): inyeccion de fallas. Termina el proceso de golpe (como un
// crash real), sin apagado ordenado, para que la replica deje de responder
// mientras sigue registrada en el ALB. `aws ecs stop-task` no sirve para esto:
// ECS retira primero la tarea del balanceador y no habria falla que medir.
// Solo existe si FAULT_INJECTION_ENABLED=true y exige X-Fault-Token.
@Controller('admin/fallas')
export class FallasController {
  @Post('caida')
  @HttpCode(202)
  caida(@Headers('x-fault-token') token: string | undefined) {
    if (process.env.FAULT_INJECTION_ENABLED !== 'true') {
      throw new NotFoundException();
    }
    const esperado = process.env.FAULT_INJECTION_TOKEN;
    if (esperado && token !== esperado) {
      throw new ForbiddenException();
    }
    const replica = instancia();
    console.log(
      JSON.stringify({
        ts: new Date().toISOString(),
        evento: 'falla_inyectada',
        replica,
      }),
    );
    // Se responde primero y luego se termina el proceso de golpe (sin cerrar
    // conexiones ni avisar al ALB). En el contenedor Node es el PID 1 y el
    // kernel ignora el SIGKILL que el PID 1 se envia a si mismo, por eso, si
    // sigue vivo, se sale con process.exit(137): el mismo codigo de un SIGKILL.
    setTimeout(() => {
      try {
        process.kill(process.pid, 'SIGKILL');
      } catch {
        /* sin efecto como PID 1 */
      }
      setTimeout(() => process.exit(137), 20);
    }, 100);
    return { replica, accion: 'caida abrupta en 100 ms' };
  }
}
