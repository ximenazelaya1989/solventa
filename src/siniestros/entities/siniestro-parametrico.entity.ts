import { ChildEntity, Column } from 'typeorm';
import { Siniestro } from './siniestro.entity';

@ChildEntity('parametrico')
export class SiniestroParametrico extends Siniestro {
  @Column({ type: 'jsonb', nullable: true })
  datosEventoParametrico!: Record<string, any> | null; // ej. sensor, umbral disparado

  @Column({ type: 'varchar', unique: true, nullable: true })
  claveIdempotenciaPago!: string | null; // evita duplicar el pago parametrico automatico
}
