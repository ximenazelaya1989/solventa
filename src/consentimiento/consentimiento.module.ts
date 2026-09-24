import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Consentimiento } from './entities/consentimiento.entity';

@Module({
  imports: [TypeOrmModule.forFeature([Consentimiento])],
})
export class ConsentimientoModule {}
