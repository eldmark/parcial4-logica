import alterer from "../../tests/fixtures/yaml/alterer_complement_ab.yaml?raw";
import recognizer from "../../tests/fixtures/yaml/recognizer_w_hash_w.yaml?raw";
import reverse from "../../tests/fixtures/yaml/alterer_reverse_ab.yaml?raw";

export const EXAMPLES = [
  { label: "Reconocedora: w#w", yaml: recognizer },
  { label: "Alteradora: complemento a↔b", yaml: alterer },
  { label: "Alteradora: invertir cadena", yaml: reverse },
];
