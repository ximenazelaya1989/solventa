import { IsBoolean, IsObject, IsOptional } from 'class-validator';

export class PublicarReglaDto {
  @IsObject()
  factores!: Record<string, number>;

  @IsOptional()
  @IsBoolean()
  fallaSanityCheck?: boolean;
}