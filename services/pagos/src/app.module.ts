import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { join } from 'path';
import { HealthController } from './health.controller';
import { Pago } from './entities/pago.entity';
import { PagosController } from './pagos/pagos.controller';
import { PagosService } from './pagos/pagos.service';
import { PasarelaClient } from './pagos/pasarela.client';
import { FallasController } from './admin/fallas.controller';

const ms = (valor: string | undefined, porDefecto: number) =>
  Number(valor ?? porDefecto);

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
      // Aurora/RDS PostgreSQL exigen TLS (rds.force_ssl). En local va en false.
      ssl:
        process.env.DB_SSL === 'true' ? { rejectUnauthorized: false } : false,
      // EXP-006 (H7.2.1): durante la conmutacion por error de Aurora, Pagos debe
      // fallar rapido (y no quedarse colgado en conexiones a la escritora caida)
      // para que Siniestros reintente contra el endpoint escritor ya promovido.
      extra: {
        max: Number(process.env.DB_POOL_MAX ?? 10),
        connectionTimeoutMillis: ms(process.env.DB_CONNECT_TIMEOUT_MS, 2000),
        query_timeout: ms(process.env.DB_QUERY_TIMEOUT_MS, 5000),
        statement_timeout: ms(process.env.DB_QUERY_TIMEOUT_MS, 5000),
        idleTimeoutMillis: ms(process.env.DB_IDLE_TIMEOUT_MS, 10000),
      },
      // Al arrancar, dos replicas pueden sincronizar el esquema a la vez:
      // si una choca con la otra, Nest reintenta la conexion.
      retryAttempts: 10,
      retryDelay: 3000,
    }),
    TypeOrmModule.forFeature([Pago]),
  ],
  controllers: [HealthController, PagosController, FallasController],
  providers: [PagosService, PasarelaClient],
})
export class AppModule {}
