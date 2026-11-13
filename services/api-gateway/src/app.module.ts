import { Module } from '@nestjs/common';
import { HealthController } from './health.controller';
import { CotizacionesController } from './cotizaciones.controller';
import { CuotaSocioModule } from './cuota-socio/cuota-socio.module';

@Module({
  imports: [CuotaSocioModule], // EXP-008: cuota por socio (RATE_LIMIT_ENABLED)
  controllers: [HealthController, CotizacionesController],
})
export class AppModule {}
