import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Cliente } from './entities/cliente.entity';
import { IdentidadCredencial } from './entities/identidad-credencial.entity';
import { IdentidadService } from './identidad.service';
import { IdentidadController } from './identidad.controller';

@Module({
  imports: [TypeOrmModule.forFeature([Cliente, IdentidadCredencial])],
  controllers: [IdentidadController],
  providers: [IdentidadService],
  exports: [IdentidadService],
})
export class IdentidadModule {}
