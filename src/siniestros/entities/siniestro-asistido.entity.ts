import { ChildEntity } from 'typeorm';
import { Siniestro } from './siniestro.entity';

@ChildEntity('asistido')
export class SiniestroAsistido extends Siniestro {}
