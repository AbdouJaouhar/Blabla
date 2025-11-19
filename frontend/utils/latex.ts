export function cleanLatex(text: string): string {
    if (typeof text !== "string") return text;
    text = text.replace(/\\\(([\s\S]*?)\\\)/g, (_, inner) => `$${inner}$`);
    text = text.replace(/\\\[([\s\S]*?)\\\]/g, (_, inner) => `$${inner}$`);
    return text;
}
