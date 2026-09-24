import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { PerfilRiesgo } from './entities/perfil-riesgo.entity';
import { PerfilamientoService } from './perfilamiento.service';

@Module({
  imports: [TypeOrmModule.forFeature([PerfilRiesgo])],
  providers: [PerfilamientoService],
  exports: [PerfilamientoService],
})
export class PerfilamientoModule {}