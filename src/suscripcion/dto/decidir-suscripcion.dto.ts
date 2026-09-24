import { IsUUID } from 'class-validator';

export class DecidirSuscripcionDto {
  @IsUUID()
  cotizacionId!: string;
}
