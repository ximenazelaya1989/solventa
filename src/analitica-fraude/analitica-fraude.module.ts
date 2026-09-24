import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { MotorDeteccionFraude } from './entities/motor-deteccion-fraude.entity';

@Module({
  imports: [TypeOrmModule.forFeature([MotorDeteccionFraude])],
})
export class AnaliticaFraudeModule {}
