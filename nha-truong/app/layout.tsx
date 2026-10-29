import type {Metadata} from 'next';
import './globals.css';
export const metadata:Metadata={title:'Thầy Được | Quản lý dạy học nhà trường',description:'Hệ thống nhiều môn học, giáo viên và học sinh. Quản trị độc lập với trung tâm.'};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="vi"><body>{children}</body></html>}
