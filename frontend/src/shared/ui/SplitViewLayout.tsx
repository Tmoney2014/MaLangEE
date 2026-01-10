import React from "react";
import Image from "next/image";
import { GlassCard } from "./GlassCard";

interface SplitViewLayoutProps {
  leftChildren?: React.ReactNode;
  rightChildren: React.ReactNode;
  bgImage?: string;
  leftColSpan?: number; // 왼쪽 영역의 그리드 비율 (1-11)
  rightColSpan?: number; // 오른쪽 영역의 그리드 비율 (1-11)
}

export const SplitViewLayout = ({
  leftChildren,
  rightChildren,
  bgImage = "/images/login-bg-01.png", // 기본 배경 설정
  leftColSpan = 6, // 기본값 6/12
  rightColSpan = 6, // 기본값 6/12
}: SplitViewLayoutProps) => {
  return (
    <div className="relative flex h-screen w-full flex-col items-center justify-center overflow-hidden text-[#1F1C2B]">
      {/* Background Image */}
      <Image src={bgImage} alt="Background" fill priority sizes="100vw" className="object-cover" />

      <div className="relative mx-auto grid h-full w-full max-w-7xl grid-cols-1 gap-6 px-6 py-12 md:grid-cols-12 md:gap-8 md:px-12">
        {/* Left Content Section */}
        <div
          className="col-span-1 flex flex-col items-start justify-center gap-6"
          style={{
            gridColumn: `span ${leftColSpan} / span ${leftColSpan}`,
          }}
        >
          <div className="text-lg font-semibold text-[#5F51D9]">MalangEE</div>
          <div className="relative flex items-center gap-6">
            <div className="relative flex items-center justify-center">
              <Image
                src="/images/malangee.svg"
                alt="MalangEE"
                width={128}
                height={128}
                priority
                className="object-contain"
              />
            </div>
          </div>
          {leftChildren && <div className="space-y-2">{leftChildren}</div>}
        </div>

        {/* Right Content Section */}
        <div
          className="relative col-span-1 flex items-center justify-center"
          style={{
            gridColumn: `span ${rightColSpan} / span ${rightColSpan}`,
          }}
        >
          <GlassCard withBackground={false} className="!h-full !min-h-0">
            {rightChildren}
          </GlassCard>
        </div>
      </div>
    </div>
  );
};

