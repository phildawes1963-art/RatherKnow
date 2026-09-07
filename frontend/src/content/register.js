// Locked-copy register. Single source for claims-register-governed strings.
// Never inline these in JSX; never edit locked_copy.json without regenerating hashes.
import LOCKED from './locked_copy.json';

export const REGISTER = LOCKED;
export const TIER_STATEMENTS = LOCKED.tier_statements;
export const TIER_CHIPS = LOCKED.tier_chips;
export const PROMISES = LOCKED.promises;
export const REFUSALS = LOCKED.refusals;
export const SAFETY = LOCKED.safety;
export const FLAG = LOCKED.flag_check;
export const POSITION_COPY = LOCKED.position;
export const LANDING = LOCKED.landing;
export const METHOD_NOTE = LOCKED.methodology_note;
export const SAMPLES_COPY = LOCKED.samples;
export const ATTRIBUTION = LOCKED.attribution;
export const DISCLAIMER = LOCKED.disclaimer;
