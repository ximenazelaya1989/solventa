import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

@Entity('motor_deteccion_fraude')
export class MotorDeteccionFraude {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  // TODO(analitica-fraude): definir por el dueño del modulo los valores validos de patronDetectado, nivelRiesgo y estado
  @Column({ type: 'varchar' })
  patronDetectado!: string;

  @Column({ type: 'varchar' })
  nivelRiesgo!: string;

  @Column({ type: 'varchar' })
  estado!: string;

  @Column({ type: 'uuid' })
  siniestroId!: string;

  @Column({ type: 'uuid', nullable: true })
  pagoId!: string | null;
}
