import { Helmet } from "react-helmet";
import { useLocation } from "react-router";

const Canonical = () => {
    const location = useLocation();

    const preferredDomain = "nextbus.org.uk";

    const canonicalUrl = `https://${preferredDomain}${location.pathname}${location.search}`;

    return (
        <Helmet>
            <link rel="canonical" href={canonicalUrl} />
        </Helmet>
    );
};

export default Canonical;
