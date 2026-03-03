import {
  ChessKnight,
  Anvil,
  Zap,
  Factory,
  Droplet,
  Rocket,
  Radiation,
  Citrus,
  Coffee,
  Wine,
  Diamond,
  CupSoda,
  Bean,
  Shell,
  Candy,
  Turtle,
  Fish,
  Ribbon,
  Flower2,
  Shirt,
  ToyBrick,
  Sparkles,
  SprayCan,
  PawPrint,
  TreePalm,
  Gem,
  Box,
  Mountain,
  Leaf,
  Snowflake,
  Bone,
  Sprout,
  TreePine,
  Flower,
  PiggyBank,
  Hexagon,
  Coins,
  Palette,
  Flame,
  FlaskConical,
  Landmark,
  Luggage,
  UserRound,
  Church,
} from "lucide-react";
import { CIV6_COLORS } from "./civ-colors";

// ── Strategic resource icons & colors ────────────────────────────────────────

export const RESOURCE_META: Record<
  string,
  { icon: React.ComponentType<React.SVGProps<SVGSVGElement>>; color: string }
> = {
  HORSES: { icon: ChessKnight, color: CIV6_COLORS.horses },
  IRON: { icon: Anvil, color: CIV6_COLORS.iron },
  NITER: { icon: Zap, color: CIV6_COLORS.niter },
  COAL: { icon: Factory, color: CIV6_COLORS.coal },
  OIL: { icon: Droplet, color: CIV6_COLORS.oil },
  ALUMINUM: { icon: Rocket, color: CIV6_COLORS.aluminum },
  URANIUM: { icon: Radiation, color: CIV6_COLORS.uranium },
};

// ── Era age colors ───────────────────────────────────────────────────────────

export const AGE_COLORS: Record<string, string> = {
  GOLDEN: CIV6_COLORS.golden,
  HEROIC: CIV6_COLORS.heroic,
  DARK: CIV6_COLORS.dark,
  NORMAL: CIV6_COLORS.normal,
};

// ── Luxury resource icons & colors ───────────────────────────────────────────

export const LUXURY_META: Record<
  string,
  { icon: React.ComponentType<React.SVGProps<SVGSVGElement>>; color: string }
> = {
  // Fruits & plants
  CITRUS: { icon: Citrus, color: "#E8A630" },
  COCOA: { icon: Bean, color: "#6B3A2A" },
  COFFEE: { icon: Coffee, color: "#5C3A1A" },
  COTTON: { icon: Flower2, color: "#C4B8A8" },
  DYES: { icon: Palette, color: "#9B3B8C" },
  INCENSE: { icon: Flame, color: "#B07040" },
  OLIVES: { icon: TreePalm, color: "#6B7A3A" },
  SILK: { icon: Ribbon, color: "#C4445C" },
  SPICES: { icon: Sprout, color: "#A85C30" },
  SUGAR: { icon: Candy, color: "#D4A0C0" },
  TEA: { icon: CupSoda, color: "#5A8C4A" },
  TOBACCO: { icon: Leaf, color: "#7A6030" },
  WINE: { icon: Wine, color: "#8B2252" },
  HONEY: { icon: Hexagon, color: "#D4A020" },
  // Minerals & gems
  DIAMONDS: { icon: Diamond, color: "#7CB8DC" },
  GYPSUM: { icon: Mountain, color: "#C4B898" },
  JADE: { icon: Gem, color: "#4A9A5A" },
  MARBLE: { icon: Box, color: "#B8B0A4" },
  MERCURY: { icon: Droplet, color: "#A0A8B0" },
  SALT: { icon: Snowflake, color: "#C8C0B0" },
  SILVER: { icon: Coins, color: "#A0A8B4" },
  AMBER: { icon: Gem, color: "#D4983C" },
  // Animals
  FURS: { icon: PawPrint, color: "#8B6E50" },
  IVORY: { icon: Bone, color: "#D8D0C0" },
  PEARLS: { icon: Shell, color: "#C8B8C8" },
  TRUFFLES: { icon: PiggyBank, color: "#8C7060" },
  WHALES: { icon: Fish, color: "#4A7A9A" },
  TURTLES: { icon: Turtle, color: "#5A8A6A" },
  // Great Merchant exclusives
  COSMETICS: { icon: Sparkles, color: "#D490A0" },
  JEANS: { icon: Shirt, color: "#4A6A9A" },
  PERFUME: { icon: SprayCan, color: "#B070B8" },
  TOYS: { icon: ToyBrick, color: "#D45040" },
  // City-state exclusives
  CINNAMON: { icon: TreePine, color: "#9A6830" },
  CLOVES: { icon: Flower, color: "#7A5A3A" },
  // Scenario
  GOLD_ORE: { icon: Coins, color: "#D4A853" },
};

// ── Great Person class colors ────────────────────────────────────────────────

export const GP_COLORS: Record<string, string> = {
  GREAT_PERSON_CLASS_GREAT_SCIENTIST: CIV6_COLORS.science,
  GREAT_PERSON_CLASS_GREAT_ENGINEER: CIV6_COLORS.production,
  GREAT_PERSON_CLASS_GREAT_MERCHANT: CIV6_COLORS.goldDark,
  GREAT_PERSON_CLASS_GREAT_GENERAL: CIV6_COLORS.military,
  GREAT_PERSON_CLASS_GREAT_ADMIRAL: CIV6_COLORS.marine,
  GREAT_PERSON_CLASS_GREAT_PROPHET: CIV6_COLORS.faith,
  GREAT_PERSON_CLASS_GREAT_WRITER: CIV6_COLORS.culture,
  GREAT_PERSON_CLASS_GREAT_ARTIST: CIV6_COLORS.tourism,
  GREAT_PERSON_CLASS_GREAT_MUSICIAN: CIV6_COLORS.favor,
};

// ── Victory type display metadata ────────────────────────────────────────────

export const VICTORY_TYPES = [
  {
    label: "Science",
    key: "sci_vp" as const,
    max: 4,
    color: CIV6_COLORS.science,
    icon: FlaskConical,
  },
  {
    label: "Diplo",
    key: "diplo_vp" as const,
    max: 20,
    color: CIV6_COLORS.favor,
    icon: Landmark,
  },
  {
    label: "Tourism",
    key: "tourism" as const,
    color: CIV6_COLORS.tourism,
    icon: Luggage,
  },
  {
    label: "Domestic",
    key: "staycationers" as const,
    color: CIV6_COLORS.goldMetal,
    icon: UserRound,
  },
  {
    label: "Religion",
    key: "religion_cities" as const,
    color: CIV6_COLORS.faith,
    icon: Church,
  },
];
