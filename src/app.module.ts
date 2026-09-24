import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { PolizasModule } from './polizas/polizas.module';
import { SuscripcionModule } from './suscripcion/suscripcion.module';
import { IdentidadModule } from './identidad/identidad.module';
import { ConsentimientoModule } from './consentimiento/consentimiento.module';
import { PerfilamientoModule } from './perfilamiento/perfilamiento.module';
import { CotizacionModule } from './cotizacion/cotizacion.module';
import { SiniestrosModule } from './siniestros/siniestros.module';
import { PagosModule } from './pagos/pagos.module';
import { ReaseguroModule } from './reaseguro/reaseguro.module';
import { AnaliticaFraudeModule } from './analitica-fraude/analitica-fraude.module';
import { ReporteriaModule } from './reporteria/reporteria.module';
import { IntegracionesModule } from './integraciones/integraciones.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    TypeOrmModule.forRoot({
      type: 'postgres',
      host: process.env.DB_HOST,
      port: Number(process.env.DB_PORT),
      username: process.env.DB_USER,
      password: process.env.DB_PASSWORD,
      database: process.env.DB_NAME,
      autoLoadEntities: true,
      synchronize: process.env.NODE_ENV !== 'production',
    }),
    PolizasModule,
    SuscripcionModule,
    IdentidadModule,
    ConsentimientoModule,
    PerfilamientoModule,
    CotizacionModule,
    SiniestrosModule,
    PagosModule,
    ReaseguroModule,
    AnaliticaFraudeModule,
    ReporteriaModule,
    IntegracionesModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}