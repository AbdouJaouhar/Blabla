type Props = {
    urls: string[];
    onRemove: (index: number) => void;
};

export default function ImagePreview({ urls, onRemove }: Props) {
    return (
        <div className="prompt-image-preview flex gap-3 flex-wrap flex-row">
            {urls.map((url, idx) => (
                <div
                    key={idx}
                    className="relative aspect-square min-w-[8rem] max-w-[50px] rounded-lg overflow-hidden border border-purple-500 mb-[1rem] rounded-md"
                >
                    <img
                        src={url}
                        alt=""
                        className="w-full h-full object-cover"
                    />

                    <button
                        onClick={() => onRemove(idx)}
                        className="absolute top-1 right-1 bg-white text-black text-xs px-1.5 py-0.5 rounded cursor-pointer"
                    >
                        ✕
                    </button>
                </div>
            ))}
        </div>
    );
}
