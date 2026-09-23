import { IsInt, Min } from 'class-validator';

export class AplicarReglaDto {
  @IsInt()
  @Min(1)
  version!: number;
}