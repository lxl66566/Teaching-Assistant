import React, { useMemo, useState, useCallback } from "react";
import ForceGraph2D from "react-force-graph-2d";

interface Node {
  id: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number;
  fy?: number;
  neighbors?: Node[];
  links?: Link[];
  __bckgDimensions?: number[]; // 添加此属性以避免any
}

interface Link {
  source: string | Node;
  target: string | Node;
  label?: string;
}

interface GraphData {
  nodes: Node[];
  edges: Link[];
}

interface KnowledgeGraphProps {
  graphData: GraphData;
}

const NODE_R = 5; // 节点半径，用于高亮环
const NODE_TEXT_SIZE = 14; // 节点文本大小
const LINK_TEXT_SIZE = 10; // 链接文本大小

const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({ graphData }) => {
  const [highlightNodes, setHighlightNodes] = useState(new Set<Node>());
  const [highlightLinks, setHighlightLinks] = useState(new Set<Link>());
  const [hoverNode, setHoverNode] = useState<Node | null>(null);

  // 转换数据格式以适应 react-force-graph-2d
  const data = useMemo(() => {
    const nodes = graphData.nodes.map((node) => ({ ...node }));
    const links = graphData.edges.map((edge) => ({ ...edge }));

    // 交叉链接节点对象，用于高亮功能
    links.forEach((link) => {
      const a = nodes.find((node) => node.id === link.source);
      const b = nodes.find((node) => node.id === link.target);
      if (a && b) {
        if (!a.neighbors) {
          a.neighbors = [];
        }
        if (!b.neighbors) {
          b.neighbors = [];
        }
        a.neighbors.push(b);
        b.neighbors.push(a);

        if (!a.links) {
          a.links = [];
        }
        if (!b.links) {
          b.links = [];
        }
        a.links.push(link);
        b.links.push(link);
      }
    });

    return { nodes, links };
  }, [graphData]);

  const updateHighlight = useCallback(() => {
    setHighlightNodes(new Set(highlightNodes));
    setHighlightLinks(new Set(highlightLinks));
  }, [highlightNodes, highlightLinks]);

  const handleNodeHover = useCallback(
    (node: Node | null) => {
      highlightNodes.clear();
      highlightLinks.clear();
      if (node) {
        highlightNodes.add(node);
        node.neighbors?.forEach((neighbor) => highlightNodes.add(neighbor));
        node.links?.forEach((link) => highlightLinks.add(link));
      }

      setHoverNode(node || null);
      updateHighlight();
    },
    [highlightNodes, highlightLinks, updateHighlight],
  );

  const handleLinkHover = useCallback(
    (link: Link | null) => {
      highlightNodes.clear();
      highlightLinks.clear();

      if (link) {
        highlightLinks.add(link);
        const sourceNode = data.nodes.find((n) => n.id === (link.source as Node).id || n.id === link.source);
        const targetNode = data.nodes.find((n) => n.id === (link.target as Node).id || n.id === link.target);
        if (sourceNode) highlightNodes.add(sourceNode);
        if (targetNode) highlightNodes.add(targetNode);
      }

      updateHighlight();
    },
    [highlightNodes, highlightLinks, updateHighlight, data.nodes],
  );

  const nodeCanvasObject = useCallback(
    (node: Node, ctx: CanvasRenderingContext2D, globalScale: number) => {
      // 如果节点被高亮，先绘制环
      if (highlightNodes.has(node)) {
        ctx.beginPath();
        ctx.arc(node.x!, node.y!, NODE_R * 1.4, 0, 2 * Math.PI, false);
        ctx.fillStyle = node === hoverNode ? "red" : "orange";
        ctx.fill();
      }

      const label = node.id;
      const fontSize = NODE_TEXT_SIZE / globalScale;
      ctx.font = `${fontSize}px Sans-Serif`;
      const textWidth = ctx.measureText(label).width;
      const bckgDimensions: [number, number] = [textWidth, fontSize].map((n) => n + fontSize * 0.2) as [number, number]; // some padding

      // 绘制背景
      ctx.fillStyle = "rgba(255, 255, 255, 0.8)";
      ctx.fillRect(node.x! - bckgDimensions[0] / 2, node.y! - bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1]);

      // 绘制文本
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = highlightNodes.has(node) ? "red" : "#333"; // 高亮节点颜色
      ctx.fillText(label, node.x!, node.y!);

      // 存储背景尺寸，用于 nodePointerAreaPaint
      node.__bckgDimensions = bckgDimensions;
    },
    [highlightNodes, hoverNode],
  );

  const nodePointerAreaPaint = useCallback((node: Node, color: string, ctx: CanvasRenderingContext2D) => {
    ctx.fillStyle = color;
    const bckgDimensions = node.__bckgDimensions;
    if (bckgDimensions) {
      ctx.fillRect(node.x! - bckgDimensions[0] / 2, node.y! - bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1]);
    }
  }, []);

  return (
    <ForceGraph2D
      graphData={data}
      nodeRelSize={NODE_R}
      autoPauseRedraw={false}
      linkWidth={(link) => (highlightLinks.has(link) ? 5 : 1)}
      linkDirectionalParticles={4}
      linkDirectionalParticleWidth={(link) => (highlightLinks.has(link) ? 4 : 0)}
      nodeCanvasObject={nodeCanvasObject} // 文本渲染和高亮环
      nodePointerAreaPaint={nodePointerAreaPaint} // 鼠标区域绘制
      onNodeHover={handleNodeHover}
      onLinkHover={handleLinkHover}
      linkCanvasObject={(link, ctx, globalScale) => {
        const start = link.source as Node;
        const end = link.target as Node;

        // 绘制链接
        ctx.beginPath();
        ctx.moveTo(start.x!, start.y!);
        ctx.lineTo(end.x!, end.y!);
        ctx.lineWidth = highlightLinks.has(link) ? 5 : 1;
        ctx.strokeStyle = highlightLinks.has(link) ? "red" : "#ccc";
        ctx.stroke();

        // 绘制链接标签
        if (link.label) {
          const label = link.label;
          const fontSize = LINK_TEXT_SIZE / globalScale;
          ctx.font = `${fontSize}px Sans-Serif`;
          const textWidth = ctx.measureText(label).width;
          const x = (start.x! + end.x!) / 2;
          const y = (start.y! + end.y!) / 2;

          ctx.fillStyle = "rgba(255, 255, 255, 0.8)";
          ctx.fillRect(x - textWidth / 2 - 2, y - fontSize / 2 - 2, textWidth + 4, fontSize + 4);
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillStyle = "#333";
          ctx.fillText(label, x, y);
        }
      }}
    />
  );
};

export default KnowledgeGraph;
