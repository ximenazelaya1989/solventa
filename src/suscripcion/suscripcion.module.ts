import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Suscripcion } from './entities/suscripcion.entity';
import { SuscripcionService } from './suscripcion.service';
import { SuscripcionController } from './suscripcion.controller';
import { PolizasModule } from '../polizas/polizas.module';
import { PerfilamientoModule } from '../perfilamiento/perfilamiento.module';
import { CotizacionModule } from '../cotizacion/cotizacion.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([Suscripcion]),
    PolizasModule,
    PerfilamientoModule,
    CotizacionModule,
  ],
  controllers: [SuscripcionController],
  providers: [SuscripcionService],
})
export class SuscripcionModule {}