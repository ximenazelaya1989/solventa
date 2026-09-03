import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Cliente } from './entities/cliente.entity';
import { Consentimiento } from './entities/consentimiento.entity';

@Module({
  imports: [TypeOrmModule.forFeature([Cliente, Consentimiento])],
})
export class IdentidadModule {}