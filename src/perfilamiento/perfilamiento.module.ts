import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { PerfilRiesgo } from './entities/perfil-riesgo.entity';
import { PerfilamientoService } from './perfilamiento.service';
import { PerfilamientoController } from './perfilamiento.controller';
import { IdentidadModule } from '../identidad/identidad.module';
import { ConsentimientoModule } from '../consentimiento/consentimiento.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([PerfilRiesgo]),
    IdentidadModule,
    ConsentimientoModule,
  ],
  controllers: [PerfilamientoController],
  providers: [PerfilamientoService],
  exports: [PerfilamientoService],
})
export class PerfilamientoModule {}
