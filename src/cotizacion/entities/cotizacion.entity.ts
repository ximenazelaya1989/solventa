import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

@Entity('cotizaciones')
export class Cotizacion {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'float' })
  prima!: number;

  @Column({ type: 'uuid' })
  clienteId!: string;

  @Column({ type: 'uuid' })
  productoId!: string;

  @Column({ type: 'uuid', nullable: true })
  socioDistribucionId!: string | null;
}