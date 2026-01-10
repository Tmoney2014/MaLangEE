import { FC } from "react";
import Image from "next/image";
import "./MicButton.css";

interface MicButtonProps {
  isListening: boolean;
  onClick: () => void;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export const MicButton: FC<MicButtonProps> = ({
  isListening,
  onClick,
  size = "md",
  className = "",
}) => {
  const sizeClasses = {
    sm: "mic-container-sm",
    md: "mic-container-md",
    lg: "mic-container-lg",
  };

  const iconSizes = {
    sm: 20,
    md: 28,
    lg: 36,
  };

  return (
    <div
      className={`mic-container ${sizeClasses[size]} ${isListening ? "is-listening" : ""} ${className}`}
      onClick={onClick}
    >
      {/* Waves */}
      <div className="waves">
        <div className="wave wave-1" />
        <div className="wave wave-2" />
        <div className="wave wave-3" />
      </div>

      {/* Main Mic Button */}
      <div className="mic-main">
        <Image
          src="/images/mic-icon.svg"
          alt="Microphone"
          width={iconSizes[size]}
          height={iconSizes[size]}
          priority
        />
      </div>
    </div>
  );
};
