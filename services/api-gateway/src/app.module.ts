import { Module } from '@nestjs/common';
import { HealthController } from './health.controller';
import { CotizacionesController } from './cotizaciones.controller';

@Module({
  controllers: [HealthController, CotizacionesController],
})
export class AppModule {}
