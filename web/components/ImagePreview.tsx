import { PendingImage } from "../utils/types"

type Props = {
    urls: string[];
    onRemove: (index: number) => void;
};

export default function ImagePreview({ urls, onRemove }: Props) {
    return (
        <div className="prompt-image-preview">
            {urls.map((image_preview, idx) => (
                <div
                    key={idx}
                    className="prompt-uploaded-image"
                >
                    <img
                        src={image_preview.url}
                        alt=""
                    />

                    <div
                        onClick={() => onRemove(image_preview.id)}
                        className="prompt-uploaded-image-btn"
                    >
                        ✕
                    </div>
                </div>
            ))}
        </div>
    );
}
