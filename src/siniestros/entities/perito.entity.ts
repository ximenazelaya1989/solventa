import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

@Entity('peritos')
export class Perito {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'varchar' })
  nombre!: string;

  @Column({ type: 'varchar' })
  especialidad!: string;
}
