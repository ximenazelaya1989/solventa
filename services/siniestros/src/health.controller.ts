import { Controller, Get } from '@nestjs/common';

// Liveness: solo comprueba que el proceso esta vivo, sin consultar BD ni
// dependencias externas (asi un ALB no retira el servicio por una caida ajena).
@Controller('health')
export class HealthController {
  @Get()
  health() {
    return { status: 'ok', servicio: process.env.SERVICE_NAME ?? 'siniestros' };
  }
}
