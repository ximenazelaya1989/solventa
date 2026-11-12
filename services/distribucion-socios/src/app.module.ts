import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { join } from 'path';
import { HealthController } from './health.controller';
import { SociosCotizacionesController } from './exp010/socios-cotizaciones.controller'; // EXP-010
import { SemillaExp010Service } from './exp010/semilla.service'; // EXP-010

@Module({
  imports: [
    TypeOrmModule.forRoot({
      type: 'postgres',
      host: process.env.DB_HOST ?? 'localhost',
      port: Number(process.env.DB_PORT ?? 5432),
      username: process.env.DB_USER ?? 'postgres',
      password: process.env.DB_PASSWORD ?? 'postgres',
      database: process.env.DB_NAME,
      // Carga todas las entidades de src/entities/*.entity.ts (ya compiladas)
      entities: [join(__dirname, 'entities', '*.entity.js')],
      synchronize: process.env.DB_SYNCHRONIZE === 'true',
      // RDS PostgreSQL exige TLS (rds.force_ssl). En local va en false. (EXP-010)
      ssl:
        process.env.DB_SSL === 'true' ? { rejectUnauthorized: false } : false,
      extra: { max: Number(process.env.DB_POOL_MAX ?? 10) },
    }),
  ],
  controllers: [HealthController, SociosCotizacionesController],
  providers: [SemillaExp010Service],
})
export class AppModule {}
