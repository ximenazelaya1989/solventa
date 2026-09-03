import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

@Entity('socios_distribucion')
export class SocioDistribucion {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'varchar' })
  canal!: string;

  @Column({ type: 'varchar' })
  apiKey!: string;
}