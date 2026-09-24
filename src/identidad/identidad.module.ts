import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Cliente } from './entities/cliente.entity';
import { IdentidadCredencial } from './entities/identidad-credencial.entity';

@Module({
  imports: [TypeOrmModule.forFeature([Cliente, IdentidadCredencial])],
})
export class IdentidadModule {}