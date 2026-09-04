import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { PolizasModule } from './polizas/polizas.module';
import { SuscripcionModule } from './suscripcion/suscripcion.module';
import { IdentidadModule } from './identidad/identidad.module';
import { PerfilamientoModule } from './perfilamiento/perfilamiento.module';
import { CotizacionModule } from './cotizacion/cotizacion.module';
import { SiniestrosModule } from './siniestros/siniestros.module';
import { PagosModule } from './pagos/pagos.module';

@Module({
  imports: [
    PolizasModule,
    SuscripcionModule,
    IdentidadModule,
    PerfilamientoModule,
    CotizacionModule,
    SiniestrosModule,
    PagosModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}