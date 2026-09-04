import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Subscripcion } from './entities/subscripcion.entity';

@Module({
  imports: [TypeOrmModule.forFeature([Subscripcion])],
})
export class SuscripcionModule {}