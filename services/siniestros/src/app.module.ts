import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { join } from 'path';
import { HealthController } from './health.controller';
import { SiniestroAsistido } from './entities/siniestro-asistido.entity';
import { IndemnizacionesController } from './indemnizaciones/indemnizaciones.controller';
import { IndemnizacionesService } from './indemnizaciones/indemnizaciones.service';
import { PagosClient } from './indemnizaciones/pagos.client';

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
      // RDS PostgreSQL exige TLS (rds.force_ssl). En local va en false.
      ssl:
        process.env.DB_SSL === 'true' ? { rejectUnauthorized: false } : false,
      extra: {
        max: Number(process.env.DB_POOL_MAX ?? 10),
        connectionTimeoutMillis: Number(process.env.DB_CONNECT_TIMEOUT_MS ?? 2000),
      },
      retryAttempts: 10,
      retryDelay: 3000,
    }),
    TypeOrmModule.forFeature([SiniestroAsistido]),
  ],
  controllers: [HealthController, IndemnizacionesController],
  providers: [IndemnizacionesService, PagosClient],
})
export class AppModule {}
