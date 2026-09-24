import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ThrottlerModule } from '@nestjs/throttler';
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
import { JobsModule } from './jobs/jobs.module';

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
      synchronize: process.env.DB_SYNCHRONIZE === 'true',
      extra: {
        max: Number(process.env.DB_POOL_MAX) || 10,
      },
    }),
    // TODO(cotizacion/integraciones): aplicar ThrottlerGuard (por ejemplo via
    // @UseGuards(ThrottlerGuard) o APP_GUARD) en los controladores de socios
    // para limitar peticiones por socio (HU5.1.2); no aplicado todavia a
    // ningun controlador, en particular no a src/cotizacion. Tambien queda
    // pendiente personalizar getTracker() para limitar por apiKey en vez de
    // por IP.
    ThrottlerModule.forRoot([
      {
        ttl: Number(process.env.THROTTLE_TTL_MS) || 60000,
        limit: Number(process.env.THROTTLE_LIMIT_POR_SOCIO) || 100,
      },
    ]),
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
    JobsModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}