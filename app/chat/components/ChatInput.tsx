import ImagePreview from "./ImagePreview";

type Props = {
    input: string;
    setInput: (v: string) => void;
    pendingImages: string[];
    setPendingImages: (fn: (prev: string[]) => string[]) => void;
    onSubmit: () => void;
    disabled?: boolean;
};

export default function ChatInput({
    input,
    setInput,
    pendingImages,
    setPendingImages,
    onSubmit,
    disabled,
}: Props) {
    // Image upload
    const handleImageUpload = async (files: FileList | null) => {
        if (!files) return;

        for (const file of Array.from(files)) {
            const formData = new FormData();
            formData.append("file", file);

            const res = await fetch("/api/upload", {
                method: "POST",
                body: formData,
            });

            if (res.ok) {
                const data = await res.json();
                setPendingImages((prev) => [...prev, data.url]);
            }
        }
    };

    return (
        <form
            className="chat-input-row"
            onSubmit={(e) => {
                e.preventDefault();
                onSubmit();
            }}
        >
            <input
                type="file"
                accept="image/*"
                multiple
                id="imageUpload"
                className="hidden"
                onChange={(e) => {
                    void handleImageUpload(e.target.files);
                    e.target.value = "";
                }}
            />
            <div className="chat-box">
                <ImagePreview
                    urls={pendingImages}
                    onRemove={(i) =>
                        setPendingImages((prev) =>
                            prev.filter((_, idx) => idx !== i),
                        )
                    }
                />
                <div className="chat-box-prompt-area">
                    <label htmlFor="imageUpload" className="chat-box-plus">
                        +
                    </label>

                    <textarea
                        value={input}
                        className="chat-box-textarea"
                        placeholder="Ask a question"
                        rows={1}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault();
                                onSubmit();
                            }
                        }}
                        onPaste={(e) => {
                            const files: File[] = [];
                            const items = e.clipboardData?.items;

                            if (items) {
                                for (let i = 0; i < items.length; i++) {
                                    const item = items[i];
                                    if (
                                        item.kind === "file" &&
                                        item.type.startsWith("image/")
                                    ) {
                                        const file = item.getAsFile();
                                        if (file) files.push(file);
                                    }
                                }
                            }

                            if (files.length > 0) {
                                void handleImageUpload(files as any);
                            }
                        }}
                    />
                    <button
                        type="submit"
                        className={` ${
                            input.trim() || pendingImages.length > 0
                                ? "bg-purple-600"
                                : "bg-gray-600 cursor-not-allowed"
                        } chat-box-send`}
                        disabled={
                            input.trim().length === 0 &&
                            pendingImages.length === 0
                        }
                    >
                        <svg
                            width="20"
                            height="20"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                            xmlns="http://www.w3.org/2000/svg"
                            class="icon"
                        >
                            <path d="M8.99992 16V6.41407L5.70696 9.70704C5.31643 10.0976 4.68342 10.0976 4.29289 9.70704C3.90237 9.31652 3.90237 8.6835 4.29289 8.29298L9.29289 3.29298L9.36907 3.22462C9.76184 2.90427 10.3408 2.92686 10.707 3.29298L15.707 8.29298L15.7753 8.36915C16.0957 8.76192 16.0731 9.34092 15.707 9.70704C15.3408 10.0732 14.7618 10.0958 14.3691 9.7754L14.2929 9.70704L10.9999 6.41407V16C10.9999 16.5523 10.5522 17 9.99992 17C9.44764 17 8.99992 16.5523 8.99992 16Z"></path>
                        </svg>
                    </button>
                </div>
            </div>
        </form>
    );
}
