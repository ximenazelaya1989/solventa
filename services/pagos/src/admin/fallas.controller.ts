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
    // Se responde primero y luego se mata el proceso con SIGKILL (sin limpieza).
    setTimeout(() => process.kill(process.pid, 'SIGKILL'), 100);
    return { replica, accion: 'caida abrupta en 100 ms' };
  }
}
