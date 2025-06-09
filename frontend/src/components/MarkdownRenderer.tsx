import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeRaw from "rehype-raw";
import "katex/dist/katex.min.css";
import React from "react";

interface MarkdownRendererProps {
  markdown: string;
}

// 基础 MarkdownRenderer 组件
const MarkdownRenderer = ({ markdown }: MarkdownRendererProps) => {
  return (
    <div className="overflow-auto-x prose min-w-0 max-w-fit text-inherit">
      <ReactMarkdown
        remarkPlugins={[remarkMath]} // 解析数学公式，如 $...$ 和 $$...$$
        rehypePlugins={[rehypeRaw, rehypeKatex]} // rehypeRaw 允许原生 HTML/SVG，rehypeKatex 渲染数学公式
      >
        {markdown}
      </ReactMarkdown>
    </div>
  );
};

// 使用 React.memo 创建记忆化版本
const MemoizedMarkdownRenderer = React.memo(
  MarkdownRenderer,
  (prevProps, nextProps) => {
    // 只有当 markdown 内容发生变化时才重新渲染
    return prevProps.markdown === nextProps.markdown;
  },
);

// 导出记忆化版本作为默认导出
export default MemoizedMarkdownRenderer;
