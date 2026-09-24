import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

export enum EstadoVerificacionKYC {
  PENDIENTE = 'pendiente',
  VERIFICADO = 'verificado',
  RECHAZADO = 'rechazado',
}

@Entity('identidad_credenciales')
export class IdentidadCredencial {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'uuid', unique: true })
  clienteId!: string;

  @Column({ type: 'varchar' })
  metodoKYC!: string;

  @Column({
    type: 'enum',
    enum: EstadoVerificacionKYC,
    default: EstadoVerificacionKYC.PENDIENTE,
  })
  estadoVerificacion!: EstadoVerificacionKYC;

  @Column({ type: 'timestamptz', nullable: true })
  fechaVerificacion!: Date | null;
}
