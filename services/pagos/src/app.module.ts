import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { join } from 'path';
import { HealthController } from './health.controller';

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
      extra: { max: Number(process.env.DB_POOL_MAX ?? 10) },
    }),
  ],
  controllers: [HealthController],
})
export class AppModule {}
