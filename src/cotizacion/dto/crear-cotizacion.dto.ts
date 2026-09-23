import { IsIn, IsOptional, IsUUID } from 'class-validator';

export class CrearCotizacionDto {
  @IsUUID()
  clienteId!: string;

  @IsUUID()
  productoId!: string;

  @IsOptional()
  @IsUUID()
  socioDistribucionId?: string;

  @IsIn(['bajo', 'medio', 'alto'])
  nivelRiesgo!: 'bajo' | 'medio' | 'alto';
}