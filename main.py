import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

model_name = "Qwen/Qwen2.5-3B-Instruct"

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,
)

tokenizer = AutoTokenizer.from_pretrained(model_name)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    dtype=torch.float16,
    quantization_config=bnb_config,
)

model.eval()

print("✅ Modèle chargé sur :", model.device)
print("Tape 'exit' pour quitter.\n")

SYSTEM_PROMPT = (
    "You are a precise and reliable assistant. "
    "Always answer the user's question directly, clearly, and logically. "
    "If the user asks for code, provide a single, self-contained example. "
    "Do not repeat the same line many times.\n"
)

# -------------------
# MÉMOIRE DE DISCUSSION
# -------------------
history = SYSTEM_PROMPT + "\n"

while True:
    user_input = input("Vous: ").strip()
    if user_input.lower() in ["exit", "quit", "stop"]:
        print("À bientôt !")
        break

    # Ajouter l'utilisateur à l’historique
    history += f"User: {user_input}\nAssistant:"

    # Génération
    inputs = tokenizer(history, return_tensors="pt").to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=1000,
        do_sample=True,
        temperature=0.4,  # plus bas => plus stable
        top_p=0.9,
        no_repeat_ngram_size=6,  # évite les boucles de n-grammes
        repetition_penalty=1.2,  # pénalise la répétition
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
    )

    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # on ne garde que la dernière réponse
    if "Assistant:" in decoded:
        reply = decoded.split("Assistant:")[-1].strip()
    else:
        reply = decoded.strip()

    print("Phi-2:", reply, "\n")

    history += f" {reply}\n"
