import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface LineChartComponentProps {
  data: Array<{ name: string; [key: string]: any }>;
  dataKeys: string[];
  colors?: string[];
  title?: string;
}

export default function LineChartComponent({ data, dataKeys, colors, title }: LineChartComponentProps) {
  const defaultColors = ['hsl(var(--primary))', 'hsl(var(--secondary))', 'hsl(var(--accent))'];
  
  return (
    <div className="w-full h-64 mt-4 mb-4">
      {title && <h4 className="text-sm font-semibold mb-2">{title}</h4>}
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} />
          <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '0.5rem'
            }}
          />
          <Legend />
          {dataKeys.map((key, index) => (
            <Line 
              key={key} 
              type="monotone" 
              dataKey={key} 
              stroke={colors?.[index] || defaultColors[index % defaultColors.length]}
              strokeWidth={2}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
