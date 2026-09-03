import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { PerfilRiesgo } from './entities/perfil-riesgo.entity';

@Module({
  imports: [TypeOrmModule.forFeature([PerfilRiesgo])],
})
export class PerfilamientoModule {}