import { Module } from '@nestjs/common';
import { HealthController } from './health.controller';
import { CotizacionesController } from './cotizaciones.controller';
import { SociosCotizacionesController } from './socios-cotizaciones.controller'; // EXP-010

@Module({
  controllers: [HealthController, CotizacionesController, SociosCotizacionesController],
})
export class AppModule {}
