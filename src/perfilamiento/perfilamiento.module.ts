import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { PerfilRiesgo } from './entities/perfil-riesgo.entity';
import { PerfilamientoService } from './perfilamiento.service';
import { PerfilamientoController } from './perfilamiento.controller';

@Module({
  imports: [TypeOrmModule.forFeature([PerfilRiesgo])],
  controllers: [PerfilamientoController],
  providers: [PerfilamientoService],
  exports: [PerfilamientoService],
})
export class PerfilamientoModule {}
