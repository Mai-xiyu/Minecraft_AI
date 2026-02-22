export class Vec3 {
  constructor(x: number, y: number, z: number);

  x: number;
  y: number;
  z: number;

  /**
   * Returns true when it is a zero vector.
   */
  isZero(): boolean;

  /**
   * Access component by index
   */
  at(id: number): number;

  /**
   * Returns an array component x, z
   */
  xz(): [number, number];

  /**
   * Returns an array component x, y
   */
  xy(): [number, number];

  /**
   * Returns an array component y, z
   */
  yz(): [number, number];

  /**
   * Returns a vector with swapped y and z
   */
  xzy(): Vec3;

  /**
   * Set own values to given x y z
   * If some components is given null, then those components won't change
   */
  set(x: number, y: number, z: number): this;

  /**
   * Set own values to values given by other
   */
  update(other: Vec3): this;

  /**
   * Return a new instance with copied values that are rounded
   */
  rounded(): Vec3;

  /**
   * Round own values to nearest integer
   */
  round(): this;

  /**
   * Return a new instance with copied values that are floored
   */
  floored(): Vec3;

  /**
   * Floor own values
   */
  floor(): this;

  /**
   * Return a new instance with copied values that are offset by dx dy and dz
   */
  offset(dx: number, dy: number, dz: number): Vec3;

  /**
   * Translate own values by dx dy and dz
   */
  translate(dx: number, dy: number, dz: number): this;

  /**
   * Add to own values by vector
   */
  add(other: Vec3): this;

  /**
   * Subtract own values by vector
   */
  subtract(other: Vec3): this;

  /**
   * Multiply own values by value from vector
   */
  multiply(other: Vec3): this;

  /**
   * Divide own values by value from vector
   */
  divide(other: Vec3): this;

  /**
   * Return a new instance with copied values that are added to by vector
   */
  plus(other: Vec3): Vec3;

  /**
   * Return a new instance with copied values that are subtracted by vector
   */
  minus(other: Vec3): Vec3;

  /**
   * Return a new instance with copied values that are scaled by number
   */
  scaled(scalar: number): Vec3;

  /**
   * Return a new instance with copied values that are absolute
   */
  abs(): Vec3;

  /**
   * Return the volume off the vector
   */
  volume(): number;

  /**
   * Return a new instance with copied values that are modulated by value from a vector
   */
  modulus(other: Vec3): Vec3;

  /**
   * Return the euclidean distance to another vector 
   */
  distanceTo(other: Vec3): number;

  /**
   * Return the squared euclidean distance to another vector
   */
  distanceSquared(other: Vec3): number;

  /**
   * Check whether two vectors are equal
   * Returns true if each components have at most `error` difference
   */
  equals(other: Vec3, error?: number): boolean;

  /**
   * Converts own values to a string representation in the format `(x, y, z)`
   */
  toString(): string;

  /**
   * Return a new instance with the same values
   */
  clone(): Vec3;

  /**
   * Return a new instance with the min values by value compared to another vector
   */
  min(other: Vec3): Vec3;

  /**
   * Return a new instance with the max values by value compared to another vector
   */
  max(other: Vec3): Vec3;

  /**
   * Returns its own euclidean norm
   */
  norm(): number;

  /**
   * Returns the dot product with another vector
   */
  dot(other: Vec3): number;

  /**
   * Returns a new instance off the cross product to another vector
   */
  cross(other: Vec3): Vec3;

  /**
   * Returns a new instance with copied values normed to the unit vector
   */
  unit(): Vec3;

  /**
   * Normalize own values
   */
  normalize(): Vec3;

  /**
   * Scale own values by a number
   */
  scale(scalar: number): this;

  /**
   * Returns the xy distance to another vector
   */
  xyDistanceTo(other: Vec3): number;

  /**
   * Returns the xz distance to another vector
   */
  xzDistanceTo(other: Vec3): number;

  /**
   * Returns the yz distance to another vector
   */
  yzDistanceTo(other: Vec3): number;

  /**
   * Returns the inner product to another vector
   */
  innerProduct(other: Vec3): number;

  /**
   * Returns the manhattan distance to another vector
   */
  manhattanDistanceTo(other: Vec3): number;

  /**
   * Returns an array with x y z in array form ie [x, y, z]
   */
  toArray(): [number, number, number];
}

export default function v(
  coordinates:
    | null
    | string
    | [number | string, number | string, number | string]
    | { x: number | string; y: number | string; z: number | string }
): Vec3;
export default function v(
  x: number | string,
  y: number | string,
  z: number | string
): Vec3;
